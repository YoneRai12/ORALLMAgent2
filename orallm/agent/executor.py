"""Execution engine for running plans."""
from __future__ import annotations

import logging
from typing import Any, Dict, List

from .tools import web_browse, file_ops

logger = logging.getLogger(__name__)

TOOLS = {
    "web_browse": web_browse.search,
    "file_ops": file_ops.handle,
}


def run_plan(plan: List[Dict[str, Any]]) -> List[Any]:
    """Execute a plan composed of tool actions.

    Parameters
    ----------
    plan:
        List of steps.  Each step is a mapping with the keys ``"tool"``
        and ``"args"`` describing which tool to invoke and the keyword
        arguments for that tool.

    Returns
    -------
    list[Any]
        Results returned from each tool invocation.
    """
    results: List[Any] = []
    for idx, step in enumerate(plan, start=1):
        tool_name = step.get("tool")
        args = step.get("args", {})
        func = TOOLS.get(tool_name)
        if func is None:
            logger.error("Unknown tool: %s", tool_name)
            raise ValueError(f"Unknown tool: {tool_name}")
        logger.info("Step %d: executing %s with args %s", idx, tool_name, args)
        result = func(**args)
        logger.debug("Step %d result: %r", idx, result)
        results.append(result)
    return results
