"""Browser session manager with screenshot streaming."""
from __future__ import annotations

import asyncio
import base64
import time
import random
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
        self.queues: list[asyncio.Queue[str]] = []
        self._pause = asyncio.Event()
        self._pause.set()
        self._playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.video_path: Optional[Path] = None
        self._context = None
        self.logger = logger
        self._capture_task: asyncio.Task | None = None

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
        path = self.frames_dir / f"{int(time.time()*1000)}.png"
        await self.page.screenshot(path=str(path))
        if self.logger:
            self.logger.log("frame", {"path": str(path)})
        with path.open("rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        for q in list(self.queues):
            await q.put(b64)

    async def _capture_loop(self) -> None:
        """Continuously capture frames for streaming."""

        while True:
            await self._wait_if_paused()
            await self._capture_once()
            await asyncio.sleep(0.5)

    async def _human_delay(self, min_delay: float = 0.1, max_delay: float = 0.3) -> None:
        """Sleep for a randomised short interval to mimic human behaviour."""
        await asyncio.sleep(random.uniform(min_delay, max_delay))

    def register(self) -> asyncio.Queue[str]:
        """Register a new consumer queue for streaming screenshots."""
        q: asyncio.Queue[str] = asyncio.Queue()
        self.queues.append(q)
        return q

    def unregister(self, q: asyncio.Queue[str]) -> None:
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
