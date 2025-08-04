"""Simple JSON lines event recorder."""
from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any, Dict


class ActionRecorder:
    """Append structured action events to a log file."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: str, data: Dict[str, Any]) -> None:
        entry = {"ts": time.time(), "event": event, **data}
        with self.path.open("a", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False)
            f.write("\n")

