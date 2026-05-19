"""Recommendation skill: heuristic ranking from metrics and evaluation."""

from __future__ import annotations

from typing import Any

from src.data.models import RecommendationCandidate


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _score_candidate(candidate: dict[str, Any], evaluation: dict[str, Any]) -> tuple[float, dict[str, float]]:
    """Weighted score in ~[0, 1] minus a small variance penalty (keeps Pydantic contract tests meaningful)."""
    metrics = candidate.get("metric_stub") or {}
    retention = _clamp01(float(metrics.get("retention") or 0.0))
    conversion = _clamp01(float(metrics.get("conversion") or 0.0))
    uncertainty = _clamp01(float(evaluation.get("uncertainty", 0.2)))

    variance_raw = float(metrics.get("variance") or 0.0)
    variance_norm = _clamp01(variance_raw)

    risk = _clamp01(float(candidate.get("risk", 0.0)))
    complexity = _clamp01(float(candidate.get("complexity", 0.0)))

    components: dict[str, float] = {
        "retention": round(retention * 0.45, 4),
        "conversion": round(conversion * 0.25, 4),
        "confidence": round((1.0 - uncertainty) * 0.20, 4),
        "risk_safety": round((1.0 - risk) * 0.05, 4),
        "simplicity": round((1.0 - complexity) * 0.05, 4),
    }
    variance_penalty = round(0.15 * variance_norm, 4)
    components["variance_penalty"] = round(-variance_penalty, 4)

    score = round(sum(components.values()), 4)
    return score, components


class RecommendationSkill:
    def run(
        self,
        candidates: list[RecommendationCandidate | dict[str, Any]],
        evaluation: dict[str, Any],
    ) -> dict:
        ranked: list[dict[str, Any]] = []
        for candidate in candidates:
            candidate_data = (
                candidate.model_dump()
                if isinstance(candidate, RecommendationCandidate)
                else dict(candidate)
            )
            score, score_components = _score_candidate(candidate_data, evaluation)
            ranked.append({**candidate_data, "score": score, "score_components": score_components})

        ranked.sort(key=lambda c: (c["score"], c.get("candidate_name", "")), reverse=True)

        return {
            "top_recommendation": ranked[0] if ranked else None,
            "ranked_candidates": ranked,
        }
