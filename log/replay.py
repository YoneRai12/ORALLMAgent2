"""Replay logged actions for debugging or auditing."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Dict, Iterator


def replay(path: Path, delay: float = 0.0) -> Iterator[Dict]:
    """Yield log entries from ``path`` optionally pausing between them."""

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                data = json.loads(line)
                yield data
                if delay:
                    time.sleep(delay)

