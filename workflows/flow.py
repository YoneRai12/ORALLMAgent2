"""Workflow scaffold for building automation pipelines."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Callable


@dataclass
class Step:
    """A single step in a workflow."""

    name: str
    action: Callable[..., None]


@dataclass
class Workflow:
    """A simple ordered collection of steps."""

    steps: List[Step] = field(default_factory=list)

    def add(self, step: Step) -> None:
        self.steps.append(step)

    def run(self) -> None:
        for step in self.steps:
            step.action()

