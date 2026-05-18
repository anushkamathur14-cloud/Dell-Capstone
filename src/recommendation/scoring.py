"""Lift-aware candidate scoring for recommendation ranking.

See docs/recommendation_agent.md for formula rationale (not UCB; v1 ranker).
"""

from __future__ import annotations

import math
from typing import Any

from src.data.models import RecommendationCandidate

DEFAULT_VARIANCE_LAMBDA = 0.2
DEFAULT_UNCERTAINTY_WEIGHT = 0.2


def score_candidate(
    candidate: RecommendationCandidate | dict[str, Any],
    evaluation: dict[str, Any],
    *,
    variance_lambda: float = DEFAULT_VARIANCE_LAMBDA,
    uncertainty_weight: float = DEFAULT_UNCERTAINTY_WEIGHT,
) -> dict[str, Any]:
    """Score one candidate; higher is better."""
    if isinstance(candidate, RecommendationCandidate):
        candidate_data = candidate.model_dump()
    else:
        candidate_data = dict(candidate)

    metric_stub = candidate_data.get("metric_stub") or {}
    retention = float(metric_stub.get("retention") or 0.0)
    variance = float(metric_stub.get("variance") or 0.0)
    uncertainty = float(evaluation.get("uncertainty", 0.1))

    variance_penalty = variance_lambda * math.sqrt(max(variance, 0.0))
    uncertainty_bonus = uncertainty_weight * (1.0 - min(max(uncertainty, 0.0), 1.0))
    estimated_lift = float(evaluation.get("estimated_lift") or evaluation.get("placeholder_lift") or 0.0)
    lift_bonus = min(estimated_lift, 0.25)

    score = retention - variance_penalty + uncertainty_bonus + lift_bonus

    return {
        **candidate_data,
        "score": round(score, 4),
        "score_components": {
            "retention": round(retention, 4),
            "variance_penalty": round(variance_penalty, 4),
            "uncertainty_bonus": round(uncertainty_bonus, 4),
            "lift_bonus": round(lift_bonus, 4),
        },
    }
