from __future__ import annotations

"""Action logging utilities."""

import json
import time
from pathlib import Path
from typing import Any, Dict


class ActionRecorder:
    """Append structured action logs to a file."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def log(self, event: str, data: Dict[str, Any]) -> None:
        entry = {"ts": time.time(), "event": event, **data}
        with self.path.open("a", encoding="utf-8") as f:
            json.dump(entry, f, ensure_ascii=False)
            f.write("\n")
