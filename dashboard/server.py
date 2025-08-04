"""FastAPI router for dashboard placeholder."""
from __future__ import annotations

import base64

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

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


@dashboard_router.websocket("/ws/stream/{session_id}")
async def stream_screen(websocket: WebSocket, session_id: str) -> None:
    """Broadcast PNG frames of a session to WebSocket clients."""

    sessions = _state.get("sessions")
    if sessions is None:
        await websocket.close()
        return
    session = sessions.get(session_id)
    if session is None or session.browser is None:
        await websocket.close()
        return
    await websocket.accept()
    queue = session.browser.register()
    try:
        while True:
            b64 = await queue.get()
            await websocket.send_bytes(base64.b64decode(b64))
    except WebSocketDisconnect:
        pass
    finally:
        session.browser.unregister(queue)

