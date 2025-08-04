"""REST API routes for file transfer and session management."""
from __future__ import annotations

import os
from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from auth.router import get_current_user
from sessions.manager import SessionManager
from agent.manager import AgentManager


router = APIRouter(prefix="/api", tags=["Manus-Like"])

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "uploaded_files"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)

session_manager: SessionManager | None = None
agent_manager: AgentManager | None = None


def set_managers(agent: AgentManager, sessions: SessionManager) -> None:
    """Configure global managers used by the router."""

    global agent_manager, session_manager
    agent_manager = agent
    session_manager = sessions


@router.post("/upload")
async def upload(file: UploadFile = File(...), user: str = Depends(get_current_user)) -> dict:
    """Receive a file and store it under ``UPLOAD_DIR``."""

    destination = UPLOAD_DIR / file.filename
    content = await file.read()
    destination.write_bytes(content)
    return {"filename": file.filename}


@router.get("/download/{rel_path:path}")
async def download(rel_path: str, user: str = Depends(get_current_user)) -> FileResponse:
    """Serve a previously uploaded file."""

    path = UPLOAD_DIR / rel_path
    if not path.is_file():
        raise HTTPException(status_code=404, detail="file not found")
    return FileResponse(path)


@router.post("/sessions")
async def create_session(user: str = Depends(get_current_user)) -> dict:
    """Create a new session and associated agent."""

    if session_manager is None or agent_manager is None:
        raise HTTPException(status_code=500, detail="managers not configured")
    agent_id = agent_manager.create_agent("default")
    session = session_manager.create(agent_id, owner=user)
    return {"session_id": session.session_id}


@router.get("/sessions/{session_id}")
async def get_session(session_id: str, user: str = Depends(get_current_user)) -> dict:
    """Retrieve metadata for a session owned by the current user."""

    if session_manager is None:
        raise HTTPException(status_code=500, detail="managers not configured")
    session = session_manager.get(session_id)
    if session is None or session.owner != user:
        raise HTTPException(status_code=404, detail="session not found")
    return session.to_dict()

