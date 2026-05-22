"""Causal evaluation skill — stub or agent loop (tools + schema validation)."""

from __future__ import annotations

from typing import Any

from src.agents.causal_agent import CausalEvaluationAgent


class CausalEvaluationSkill:
    def __init__(self, agent: CausalEvaluationAgent | None = None) -> None:
        self._agent = agent or CausalEvaluationAgent()

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        return self._agent.run(context)
