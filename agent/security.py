"""Security utilities for handling ephemeral credentials."""

from __future__ import annotations


class SessionSecrets:
    """Context manager that scrubs credentials after use."""

    def __init__(self, email: str, password: str) -> None:
        self._email = email
        self._password = password

    def __enter__(self) -> "SessionSecrets":
        self.email = self._email
        self.password = self._password
        return self

    def __exit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - simple scrubbing
        for attr in ("email", "password", "_email", "_password"):
            value = getattr(self, attr, None)
            if isinstance(value, str):
                setattr(self, attr, "\x00" * len(value))
            if hasattr(self, attr):
                delattr(self, attr)

