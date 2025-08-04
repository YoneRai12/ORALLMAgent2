"""FastAPI router for dashboard placeholder."""
from __future__ import annotations

from fastapi import APIRouter

dashboard_router = APIRouter()
_state: dict[str, object] = {}


def set_state(agent_manager, session_manager) -> None:
    """Inject global state for dashboard views."""
    _state["agents"] = agent_manager
    _state["sessions"] = session_manager


@dashboard_router.get("/dashboard")
async def dashboard_index() -> dict:
    """Return active agents and sessions for monitoring."""
    agents = _state.get("agents")
    sessions = _state.get("sessions")
    agent_list = agents.list_agents() if agents else {}
    session_list = sessions.list() if sessions else {}
    return {"agents": agent_list, "sessions": session_list}

