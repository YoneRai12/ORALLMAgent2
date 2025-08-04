"""FastAPI router for dashboard placeholder."""
from __future__ import annotations

from fastapi import APIRouter

dashboard_router = APIRouter()


@dashboard_router.get("/dashboard")
async def dashboard_index() -> dict:
    """Placeholder endpoint returning active agents and sessions."""
    # In a full implementation this would return HTML/JS frontend assets.
    return {"message": "Dashboard UI not yet implemented"}

