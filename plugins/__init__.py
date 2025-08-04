"""Plugin system for extending agent capabilities."""

from .base import Plugin
from .loader import load_plugins

__all__ = ["Plugin", "load_plugins"]

