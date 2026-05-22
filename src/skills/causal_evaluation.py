"""Causal evaluation skill — stub or agent loop (tools + schema validation)."""

from __future__ import annotations

from typing import Any

from src.agents.causal_agent import CausalEvaluationAgent


class CausalEvaluationSkill:
    def __init__(self, agent: CausalEvaluationAgent | None = None) -> None:
        self._agent = agent or CausalEvaluationAgent()

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        from src.config.settings import get_settings

        use_loop = context.get("use_causal_agent_loop")
        if use_loop is None:
            use_loop = get_settings().enable_causal_agent_loop
        return self._agent.run(context, use_agent_loop=use_loop)
