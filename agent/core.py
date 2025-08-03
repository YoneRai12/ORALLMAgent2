"""Core agent implementation.

This module provides a very small scaffold for an autonomous agent capable of
planning tasks with an LLM and executing tools step-by-step.  The actual
implementation of tool execution and reflection is left for future work.
"""
from __future__ import annotations

import os
from typing import List

from dotenv import load_dotenv

from tools import web_search

# Load environment variables when imported
load_dotenv()


class Agent:
    """Manus-style autonomous agent.

    Parameters
    ----------
    name: str
        Agent name used for logging.
    """

    def __init__(self, name: str = "agent") -> None:
        self.name = name

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
        if "web_search" in plan:
            results.append(web_search.search("example query"))
        return results
