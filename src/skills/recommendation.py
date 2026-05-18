"""Recommendation skill backed by the LangGraph recommendation agent.

Used by AdaptiveExperimentationOrchestrator after experiment generation.
See docs/recommendation_agent.md.
"""

from __future__ import annotations

from typing import Any, Optional

from src.agent.recommendation_agent import RecommendationAgent
from src.data.models import RecommendationCandidate


class RecommendationSkill:
    def __init__(self, agent: Optional[RecommendationAgent] = None) -> None:
        self._agent = agent or RecommendationAgent()

    def run(
        self,
        candidates: list[RecommendationCandidate],
        evaluation: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        return self._agent.run(candidates=candidates, evaluation=evaluation, context=context)
