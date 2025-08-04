"""Core agent implementation.

This module provides a very small scaffold for an autonomous agent capable of
planning tasks with an LLM and executing tools step-by-step.  The actual
implementation of tool execution and reflection is left for future work.
"""
from __future__ import annotations

import os
from typing import Callable, Dict, List

from dotenv import load_dotenv

# Tools are injected via plugin system; ``web_search`` is provided as default
from tools import web_search
from log.record import ActionRecorder

# Load environment variables when imported
load_dotenv()


class Agent:
    """Manus-style autonomous agent.

    Parameters
    ----------
    name: str
        Agent name used for logging.
    """

    def __init__(self, name: str = "agent", tools: Dict[str, Callable] | None = None, logger: "ActionRecorder" | None = None) -> None:
        self.name = name
        self.tools = {"web_search": web_search.search}
        if tools:
            self.tools.update(tools)
        self.logger = logger

    def plan(self, instruction: str) -> str:
        """Generate a plan using the configured LLM server."""
        from main import call_llm  # local import to avoid circular dependency

        return call_llm(f"Create a plan for: {instruction}")

    def execute(self, plan: str) -> List[str]:
        """Execute the provided plan.

        This stub implementation only supports a web_search action.
        Future implementations should parse the plan and dispatch to the
        appropriate tools while performing reflection and re-planning.
        """

        results = []
        for tool_name, tool_fn in self.tools.items():
            if tool_name in plan:
                if self.logger:
                    self.logger.log("tool_call", {"tool": tool_name})
                results.append(tool_fn("example query"))
        return results
