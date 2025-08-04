"""Base classes for plugin integration."""
from __future__ import annotations

from typing import Protocol


class Plugin(Protocol):
    """Simple plugin interface.

    Plugins can register new tools, API routes, or event handlers.  They are
    loaded dynamically at startup from a configured plugins directory.
    """

    name: str

    def setup(self) -> None:
        """Perform plugin initialization."""

