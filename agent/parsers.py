"""Utility functions for command parsing."""

from __future__ import annotations

import shlex
from typing import Dict, Tuple


def parse_kv_pairs(cmd: str) -> Tuple[Dict[str, str], str]:
    """Extract ``key=value`` pairs from ``cmd``.

    Parameters
    ----------
    cmd: str
        Command string that may contain key-value tokens like ``email=foo``.

    Returns
    -------
    tuple
        Mapping of parsed key-value pairs and the command with those tokens
        removed.
    """

    tokens = shlex.split(cmd)
    kv: Dict[str, str] = {}
    remaining: list[str] = []
    for tok in tokens:
        if "=" in tok:
            key, value = tok.split("=", 1)
            kv[key] = value
        else:
            remaining.append(tok)
    sanitized = " ".join(remaining)
    return kv, sanitized

