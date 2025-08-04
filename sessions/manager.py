from __future__ import annotations

"""Session management utilities."""

import json
import uuid
from pathlib import Path
from typing import Dict

from .session import Session
from logs.recorder import ActionRecorder
from tools.browser_session import BrowserSession


class SessionManager:
    """Create, store, and restore user sessions."""

    def __init__(self, storage: Path) -> None:
        self.storage = storage
        self.storage.mkdir(parents=True, exist_ok=True)
        self.sessions: Dict[str, Session] = {}

    def create(self, agent_id: str, owner: str) -> Session:
        """Create a new session owned by ``owner`` with its own log and browser state."""
        session_id = str(uuid.uuid4())
        session_path = self.storage / session_id
        session_path.mkdir(parents=True, exist_ok=True)
        recorder = ActionRecorder(session_path / "actions.log")
        browser = BrowserSession(session_id=session_id, save_root=self.storage, logger=recorder)
        session = Session(session_id=session_id, agent_id=agent_id, owner=owner, browser=browser, log=recorder)
        self.sessions[session_id] = session
        return session

    def get(self, session_id: str) -> Session | None:
        return self.sessions.get(session_id)

    def list(self, owner: str | None = None) -> Dict[str, str]:
        """Return mapping of session IDs to their agent IDs.

        Parameters
        ----------
        owner:
            If provided, only sessions belonging to ``owner`` are returned.
        """
        if owner:
            return {sid: s.agent_id for sid, s in self.sessions.items() if s.owner == owner}
        return {sid: s.agent_id for sid, s in self.sessions.items()}

    def save(self, session_id: str) -> None:
        """Persist session metadata to disk."""
        session = self.sessions[session_id]
        meta = session.to_dict()
        path = self.storage / session_id / "session.json"
        with path.open("w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

    def load(self, session_id: str) -> Session:
        """Load session metadata from disk and register it."""
        path = self.storage / session_id / "session.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        session = Session.from_dict(data, self.storage)
        self.sessions[session_id] = session
        return session
