"""Recommendation skill; RecommendationAgent nodes call these methods (4A)."""

from __future__ import annotations

from typing import Any, Optional

from src.data.models import RecommendationCandidate
from src.recommendation.input_checks import run_input_checks
from src.recommendation.llm_explanation import generate_recommendation_explanation
from src.recommendation.ranking import rank_scored_candidates
from src.recommendation.scoring import DEFAULT_UNCERTAINTY_WEIGHT, DEFAULT_VARIANCE_LAMBDA, score_candidate


class RecommendationSkill:
    def __init__(self, agent: Optional[Any] = None) -> None:
        self._agent = agent

    def run_prepare(self, candidates: list[Any], evaluation: dict[str, Any]) -> dict[str, Any]:
        return {"warnings": run_input_checks(candidates, evaluation)}

    def run_score(
        self,
        candidates: list[Any],
        evaluation: dict[str, Any],
        variance_lambda: float = DEFAULT_VARIANCE_LAMBDA,
        uncertainty_weight: float = DEFAULT_UNCERTAINTY_WEIGHT,
    ) -> dict[str, Any]:
        scored = [
            score_candidate(
                candidate,
                evaluation,
                variance_lambda=variance_lambda,
                uncertainty_weight=uncertainty_weight,
            )
            for candidate in candidates
        ]
        return {"scored_candidates": scored}

    def run_rank(self, scored_candidates: list[dict[str, Any]]) -> dict[str, Any]:
        ranked = rank_scored_candidates(scored_candidates)
        top = ranked[0] if ranked else None
        return {"ranked_candidates": ranked, "top_recommendation": top}

    def run_explain(
        self,
        *,
        top_recommendation: Optional[dict[str, Any]],
        ranked_candidates: list[dict[str, Any]],
        evaluation: dict[str, Any],
        warnings: list[str],
        enable_llm: bool = False,
    ) -> dict[str, Any]:
        explanation, source = generate_recommendation_explanation(
            top_recommendation=top_recommendation,
            ranked_candidates=ranked_candidates,
            evaluation=evaluation,
            warnings=warnings,
            use_llm=enable_llm,
        )
        return {"explanation": explanation, "explanation_source": source}

    def run(
        self,
        candidates: list[RecommendationCandidate],
        evaluation: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        if self._agent is not None:
            return self._agent.run(candidates=candidates, evaluation=evaluation, context=context)
        from src.agent.recommendation_agent import RecommendationAgent

        return RecommendationAgent().run(candidates=candidates, evaluation=evaluation, context=context)
