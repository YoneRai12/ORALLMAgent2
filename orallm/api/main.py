"""FastAPI application exposing the agent."""
from __future__ import annotations

from fastapi import FastAPI

from ..agent import planner, executor

app = FastAPI()


@app.post("/run")
async def run(goal: str) -> dict:
    """Create a plan for ``goal`` and execute it."""
    plan = planner.make_plan(goal)
    results = executor.run_plan(plan)
    return {"plan": plan, "results": results}
