"""Browser session manager with screenshot streaming."""
from __future__ import annotations

import asyncio
import base64
import time
from pathlib import Path
from typing import Optional

from logs.recorder import ActionRecorder

from playwright.async_api import async_playwright, Page, Browser


class BrowserSession:
    """Manage a browser automation session with screenshot capture.

    Screenshots are stored under ``save_dir/session_id`` and pushed to an
    ``asyncio.Queue`` for WebSocket streaming.
    """

    def __init__(self, session_id: str, save_root: Path, logger: ActionRecorder | None = None) -> None:
        self.session_id = session_id
        self.save_dir = save_root / session_id
        self.save_dir.mkdir(parents=True, exist_ok=True)
        # Each connected client receives frames through its own queue so that
        # screenshots can be broadcast to multiple viewers simultaneously.
        self.queues: list[asyncio.Queue[str]] = []
        self._pause = asyncio.Event()
        self._pause.set()
        self._playwright = None
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.logger = logger

    async def start(self, url: str = "about:blank") -> None:
        """Launch a browser and navigate to ``url``."""
        self._playwright = await async_playwright().start()
        self.browser = await self._playwright.chromium.launch(headless=True)
        self.page = await self.browser.new_page()
        await self.page.goto(url)
        if self.logger:
            self.logger.log("browser_start", {"url": url})
        await self._capture()

    async def goto(self, url: str) -> None:
        await self._wait_if_paused()
        assert self.page is not None
        await self.page.goto(url)
        if self.logger:
            self.logger.log("goto", {"url": url})
        await self._capture()

    async def click(self, selector: str) -> None:
        await self._wait_if_paused()
        assert self.page is not None
        await self.page.click(selector)
        if self.logger:
            self.logger.log("click", {"selector": selector})
        await self._capture()

    async def fill(self, selector: str, text: str) -> None:
        await self._wait_if_paused()
        assert self.page is not None
        await self.page.fill(selector, text)
        if self.logger:
            self.logger.log("fill", {"selector": selector})
        await self._capture()

    async def _capture(self) -> None:
        """Save screenshot to disk and enqueue base64 data."""
        assert self.page is not None
        path = self.save_dir / f"{int(time.time()*1000)}.png"
        await self.page.screenshot(path=str(path))
        with path.open("rb") as f:
            b64 = base64.b64encode(f.read()).decode()
        # Broadcast the frame to all registered queues.
        for q in list(self.queues):
            await q.put(b64)

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
        if self.browser is not None:
            await self.browser.close()
        if self._playwright is not None:
            await self._playwright.stop()
