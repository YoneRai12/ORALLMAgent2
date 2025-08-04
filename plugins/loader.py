from __future__ import annotations

"""Simple plugin loader.

New tools or integrations can be added by placing modules in the ``plugins``
directory that expose a ``setup`` function.  Each plugin receives a reference to
the application state and may register routes, tools, or background tasks.
"""

import importlib
import pkgutil
from typing import List, Protocol, Any


class SupportsSetup(Protocol):
    """Protocol for plugins exposing a ``setup`` function."""

    def setup(self, app: Any) -> None:  # pragma: no cover - runtime interface
        ...


def load_plugins(app: Any) -> List[SupportsSetup]:
    """Discover and initialise plugins within the package."""
    loaded: List[SupportsSetup] = []
    for mod in pkgutil.iter_modules(__path__):  # type: ignore[name-defined]
        if mod.name in {"base", "loader"}:
            continue
        module = importlib.import_module(f"plugins.{mod.name}")
        plugin: SupportsSetup | None = getattr(module, "plugin", None)
        if plugin is not None and hasattr(plugin, "setup"):
            plugin.setup(app)
            loaded.append(plugin)
    return loaded
