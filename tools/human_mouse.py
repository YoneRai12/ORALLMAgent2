"""Helpers for human-like mouse interactions."""
from __future__ import annotations

import asyncio
import random
from typing import Iterable

from playwright.async_api import Page


async def _bezier_path(start: tuple[float, float], end: tuple[float, float], steps: int = 20) -> Iterable[tuple[float, float]]:
    """Generate a simple quadratic Bézier curve path."""

    (x0, y0), (x2, y2) = start, end
    cx = (x0 + x2) / 2 + random.uniform(-100, 100)
    cy = (y0 + y2) / 2 + random.uniform(-100, 100)
    for i in range(1, steps + 1):
        t = i / steps
        x = (1 - t) ** 2 * x0 + 2 * (1 - t) * t * cx + t ** 2 * x2
        y = (1 - t) ** 2 * y0 + 2 * (1 - t) * t * cy + t ** 2 * y2
        yield x, y


async def human_move(page: Page, x: float, y: float) -> None:
    """Move the mouse to ``(x, y)`` using a curved path and varying speed."""

    start = await page.mouse.position()
    for px, py in _bezier_path(start, (x, y), steps=15):
        await page.mouse.move(px, py)
        await asyncio.sleep(random.uniform(0.01, 0.03))


async def human_scroll(page: Page, dx: int, dy: int) -> None:
    """Scroll with small pauses to mimic human behaviour."""

    steps = max(abs(dx), abs(dy)) // 100 + 1
    for _ in range(steps):
        await page.mouse.wheel(dx / steps, dy / steps)
        await asyncio.sleep(random.uniform(0.02, 0.05))


async def human_zoom(page: Page, delta: float) -> None:
    """Zoom the page by controlling the mouse wheel with CTRL pressed."""

    await page.keyboard.down("Control")
    await page.mouse.wheel(0, -delta * 100)
    await asyncio.sleep(random.uniform(0.05, 0.2))
    await page.keyboard.up("Control")
