from __future__ import annotations

"""Replay recorded actions."""

import json
from pathlib import Path
from typing import Dict, Iterator


def replay(path: Path) -> Iterator[Dict]:
    """Yield logged actions from ``path`` in order."""
    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)
