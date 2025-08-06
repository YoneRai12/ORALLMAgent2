"""Local text file operations."""
from __future__ import annotations

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def handle(action: str, path: str, text: Optional[str] = None) -> str:
    """Handle basic text file operations.

    Parameters
    ----------
    action:
        Operation to perform: ``"read"``, ``"append"``, or ``"write"``.
    path:
        Path to the target file.
    text:
        Text to append or write. Required for ``"append"`` and ``"write"``.

    Returns
    -------
    str
        File contents for ``"read"`` or a confirmation message for other
        operations.
    """
    if action == "read":
        try:
            with open(path, "r", encoding="utf-8") as f:
                content = f.read()
            logger.info("Read %d bytes from %s", len(content), path)
            return content
        except FileNotFoundError:
            logger.warning("File not found: %s", path)
            return ""

    if action == "append":
        if text is None:
            raise ValueError("append action requires text")
        with open(path, "a", encoding="utf-8") as f:
            f.write(text)
        logger.info("Appended %d bytes to %s", len(text), path)
        return "append ok"

    if action in {"write", "overwrite"}:
        if text is None:
            raise ValueError("write action requires text")
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)
        logger.info("Wrote %d bytes to %s", len(text), path)
        return "write ok"

    logger.error("Unknown file action: %s", action)
    raise ValueError(f"Unknown action: {action}")
