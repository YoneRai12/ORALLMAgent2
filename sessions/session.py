from __future__ import annotations

"""User session state for Manus-style agent.

Each session holds chat history, associated agent and browser automation
state. Sessions can be serialised to JSON for persistence and later
reloaded. Logging of actions is delegated to :class:`~log.record.ActionRecorder`.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from tools.browser_session import BrowserSession
from log.record import ActionRecorder


@dataclass
class Session:
    """Container for a user's interaction session.

    Parameters
    ----------
    session_id:
        Unique identifier for the session.
    agent_id:
        Identifier of the agent associated with this session.
    chat_history:
        Sequential log of user/agent messages.
    browser:
        Optional browser automation state.
    log:
        Recorder used for persistent action logging.
    """

    session_id: str
    agent_id: str
    owner: str = ""
    chat_history: List[Dict[str, str]] = field(default_factory=list)
    browser: Optional[BrowserSession] = None
    log: Optional[ActionRecorder] = None

    def to_dict(self) -> Dict[str, Any]:
        """Serialise session metadata to a dictionary."""
        return {
            "session_id": self.session_id,
            "agent_id": self.agent_id,
            "owner": self.owner,
            "chat_history": self.chat_history,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any], storage: Path) -> "Session":
        """Reconstruct a :class:`Session` from stored metadata."""
        session = cls(
            session_id=data["session_id"],
            agent_id=data["agent_id"],
            owner=data.get("owner", ""),
            chat_history=data.get("chat_history", []),
        )
        log_path = storage / data["session_id"] / "actions.log"
        session.log = ActionRecorder(log_path)
        return session
