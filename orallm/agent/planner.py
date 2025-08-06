"""Simple planner that produces a list of tool invocations."""
from __future__ import annotations

from typing import Any, Dict, List


def make_plan(goal: str) -> List[Dict[str, Any]]:
    """Create a simple plan based on the provided goal.

    The current implementation is intentionally naive and is primarily
    intended for unit testing.  It returns a single step instructing the
    agent to perform a web search using the goal as the query.

    Parameters
    ----------
    goal:
        The user's objective.

    Returns
    -------
    list[dict[str, Any]]
        A list of plan steps.  Each step contains a ``tool`` name and the
        keyword arguments to pass to that tool.
    """
    return [{"tool": "web_browse", "args": {"query": goal}}]
