"""Browser session manager with screenshot streaming.

Provides JPEG frames over an asyncio queue which can be consumed by a
WebSocket handler. The same frames are written to an ``ffmpeg`` subprocess in
MJPEG format so that an HLS stream can be produced for Safari/iOS clients.
"""
from __future__ import annotations

import asyncio
import os
import time
import random
import contextlib
from pathlib import Path
from typing import Optional

from log.record import ActionRecorder

from playwright.async_api import async_playwright, Page, Browser


class BrowserSession:
    """Manage a browser automation session with screenshot capture.

    Screenshots are stored under ``save_dir/session_id`` and pushed to an
    ``asyncio.Queue`` for WebSocket streaming.
    """

    def __init__(self, session_id: str, save_root: Path, logger: ActionRecorder | None = None) -> None:
        """Create a new browser session.

        Frames are stored under ``save_root/session_id/frames`` so they can be
        replayed later.  ``user_data_dir`` is used by Playwright to persist
        cookies and other state between runs.
        """

        self.session_id = session_id
        self.save_dir = save_root / session_id
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.frames_dir = self.save_dir / "frames"
        self.frames_dir.mkdir(exist_ok=True)
        self.user_data_dir = self.save_dir / "user_data"
        # Each connected client receives frames through its own queue so that
        # screenshots can be broadcast to multiple viewers simultaneously.
        self.queues: list[asyncio.Queue[bytes]] = []
        self._pause = asyncio.Event()
        self._pause.set()
        self._playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.video_path: Optional[Path] = None
        self._context = None
        self.logger = logger
        self._capture_task: asyncio.Task | None = None
        # ffmpeg process for HLS conversion
        self._ffmpeg: asyncio.subprocess.Process | None = None
        self.stream_fps = int(os.getenv("STREAM_FPS", "12"))
        self.png_quality = int(os.getenv("PNG_QUALITY", "70"))
        self.max_viewers = int(os.getenv("MAX_VIEWERS", "6"))

    async def start(self, url: str = "about:blank") -> None:
        """Launch a browser and navigate to ``url``."""
        self._playwright = await async_playwright().start()
        context = await self._playwright.chromium.launch_persistent_context(
            user_data_dir=str(self.user_data_dir),
            headless=True,
            record_video_dir=str(self.save_dir),
        )
        self.browser = context.browser
        self.page = context.pages[0]
        await self.page.goto(url)
        if self.logger:
            self.logger.log("browser_start", {"url": url})
        # store context for closing and get video later
        self._context = context
        # ffmpeg process for HLS output
        hls_path = self.save_dir / "master.m3u8"
        segment = os.getenv("HLS_SEGMENT_TIME", "4")
        self._ffmpeg = await asyncio.create_subprocess_exec(
            "ffmpeg",
            "-loglevel",
            "error",
            "-y",
            "-f",
            "mjpeg",
            "-i",
            "-",
            "-c:v",
            "libx264",
            "-f",
            "hls",
            "-hls_time",
            segment,
            "-hls_list_size",
            "5",
            str(hls_path),
            stdin=asyncio.subprocess.PIPE,
            stdout=asyncio.subprocess.DEVNULL,
            stderr=asyncio.subprocess.DEVNULL,
        )
        self._capture_task = asyncio.create_task(self._capture_loop())

    async def goto(self, url: str) -> None:
        await self._wait_if_paused()
        assert self.page is not None
        await self.page.goto(url)
        if self.logger:
            self.logger.log("goto", {"url": url})
        await self._human_delay()
        await self._capture_once()

    async def click(self, selector: str) -> None:
        await self._wait_if_paused()
        assert self.page is not None
        locator = self.page.locator(selector)
        box = await locator.bounding_box()
        if box:
            await self.page.mouse.move(box["x"] + box["width"] / 2, box["y"] + box["height"] / 2, steps=10)
            await self._human_delay()
        await locator.click()
        if self.logger:
            self.logger.log("click", {"selector": selector})
        await self._capture_once()

    async def fill(self, selector: str, text: str) -> None:
        await self._wait_if_paused()
        assert self.page is not None
        locator = self.page.locator(selector)
        await locator.click()
        for ch in text:
            await self.page.keyboard.type(ch)
            await self._human_delay(0.05, 0.2)
        if self.logger:
            self.logger.log("fill", {"selector": selector})
        await self._capture_once()

    async def _capture_once(self) -> None:
        """Capture a single frame to disk and broadcast it."""

        assert self.page is not None
        frame_bytes = await self.page.screenshot(type="jpeg", quality=self.png_quality)
        path = self.frames_dir / f"{int(time.time()*1000)}.jpg"
        with path.open("wb") as f:
            f.write(frame_bytes)
        if self.logger:
            self.logger.log("frame", {"path": str(path)})
        for q in list(self.queues):
            await q.put(frame_bytes)
        if self._ffmpeg and self._ffmpeg.stdin:
            try:
                self._ffmpeg.stdin.write(frame_bytes)
                await self._ffmpeg.stdin.drain()
            except Exception:
                pass

    async def _capture_loop(self) -> None:
        """Continuously capture frames for streaming."""

        while True:
            await self._wait_if_paused()
            await self._capture_once()
            await asyncio.sleep(1 / self.stream_fps)

    async def _human_delay(self, min_delay: float = 0.1, max_delay: float = 0.3) -> None:
        """Sleep for a randomised short interval to mimic human behaviour."""
        await asyncio.sleep(random.uniform(min_delay, max_delay))

    def register(self) -> asyncio.Queue[bytes] | None:
        """Register a new consumer queue for streaming screenshots."""
        if len(self.queues) >= self.max_viewers:
            return None
        q: asyncio.Queue[bytes] = asyncio.Queue()
        self.queues.append(q)
        return q

    def unregister(self, q: asyncio.Queue[bytes]) -> None:
        """Remove a previously registered consumer queue."""
        try:
            self.queues.remove(q)
        except ValueError:
            pass

    def pause(self) -> None:
        self._pause.clear()

    def resume(self) -> None:
        self._pause.set()

    async def step(self) -> None:
        self.resume()
        await asyncio.sleep(0)
        self.pause()

    async def _wait_if_paused(self) -> None:
        await self._pause.wait()

    async def close(self) -> None:
        if self._context is not None:
            try:
                await self._context.close()
                if self.page is not None and hasattr(self.page, "video"):
                    self.video_path = Path(await self.page.video.path())
            except Exception:
                self.video_path = None
        if self.browser is not None:
            await self.browser.close()
        if self._playwright is not None:
            await self._playwright.stop()
        if self._ffmpeg is not None and self._ffmpeg.stdin:
            self._ffmpeg.stdin.close()
            with contextlib.suppress(Exception):
                await self._ffmpeg.wait()
