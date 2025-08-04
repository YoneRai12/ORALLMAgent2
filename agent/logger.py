"""Logging helpers with credential masking."""

from __future__ import annotations

import logging
import re


_CRED_RE = re.compile(r"(email|pass)=[^\s]+", re.IGNORECASE)


class CredentialFilter(logging.Filter):
    """Mask sensitive key-value pairs in log messages."""

    def filter(self, record: logging.LogRecord) -> bool:  # pragma: no cover - simple substitution
        record.msg = _CRED_RE.sub(lambda m: f"{m.group(1)}=***", str(record.msg))
        return True


logger = logging.getLogger("agent")
logger.addFilter(CredentialFilter())

