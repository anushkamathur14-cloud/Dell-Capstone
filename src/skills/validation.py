"""Validation skill backed by the LangGraph validation agent.

Used by AdaptiveExperimentationOrchestrator immediately after retrieval.
See docs/validation_agent.md.
"""

from __future__ import annotations

from typing import Optional

from src.agent.validation_agent import ValidationAgent


class ValidationSkill:
    def __init__(self, agent: Optional[ValidationAgent] = None) -> None:
        self._agent = agent or ValidationAgent()

    def run(self, context: dict) -> dict:
        return self._agent.run(context)
