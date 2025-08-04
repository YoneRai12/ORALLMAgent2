"""Management of multiple sub-agents.

This module defines :class:`AgentManager`, a lightweight registry that keeps
track of active agents and allows creating or removing them dynamically.  Each
agent runs independently and can be addressed via its unique identifier.  The
implementation is intentionally minimal and serves as a scaffold for more
advanced features such as inter-agent communication or cooperative planning.
"""
from __future__ import annotations

import uuid
from typing import Dict

from .core import Agent


class AgentManager:
    """Create and manage multiple sub-agents."""

    def __init__(self, max_agents: int = 5) -> None:
        self.max_agents = max_agents
        self.agents: Dict[str, Agent] = {}

    def create_agent(self, profile: str = "default") -> str:
        """Instantiate a new agent and return its identifier."""
        if len(self.agents) >= self.max_agents:
            raise RuntimeError("maximum number of agents reached")
        agent_id = str(uuid.uuid4())
        self.agents[agent_id] = Agent(name=f"agent-{profile}-{agent_id[:8]}")
        return agent_id

    def list_agents(self) -> Dict[str, str]:
        """Return mapping of agent IDs to their names."""
        return {aid: ag.name for aid, ag in self.agents.items()}

    def get(self, agent_id: str) -> Agent | None:
        """Retrieve an agent by identifier."""
        return self.agents.get(agent_id)

    def remove(self, agent_id: str) -> None:
        """Remove an agent if it exists."""
        self.agents.pop(agent_id, None)

