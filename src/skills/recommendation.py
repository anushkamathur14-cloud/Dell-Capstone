"""Recommendation skill: heuristic ranking from metrics and evaluation."""

from __future__ import annotations

from typing import Any


def _clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def _score_candidate(candidate: dict[str, Any], evaluation: dict[str, Any]) -> tuple[float, dict[str, float]]:
    metrics = candidate.get("metric_stub") or {}
    retention = _clamp01(float(metrics.get("retention") or 0.0))
    conversion = _clamp01(float(metrics.get("conversion") or 0.0))
    uncertainty = _clamp01(float(evaluation.get("uncertainty", 0.5)))

    risk = _clamp01(float(candidate.get("risk", 0.0)))
    complexity = _clamp01(float(candidate.get("complexity", 0.0)))

    components: dict[str, float] = {
        "retention": round(retention * 0.45, 4),
        "conversion": round(conversion * 0.25, 4),
        "confidence": round((1.0 - uncertainty) * 0.20, 4),
        "risk_safety": round((1.0 - risk) * 0.05, 4),
        "simplicity": round((1.0 - complexity) * 0.05, 4),
    }
    score = sum(components.values())

    return round(score, 4), components


class RecommendationSkill:
    def run(self, candidates: list[dict], evaluation: dict) -> dict:
        ranked: list[dict[str, Any]] = []
        for candidate in candidates:
            score, score_components = _score_candidate(candidate, evaluation)
            ranked.append({**candidate, "score": score, "score_components": score_components})

        ranked.sort(key=lambda c: (c["score"], c.get("candidate_name", "")), reverse=True)

        return {
            "top_recommendation": ranked[0] if ranked else None,
            "ranked_candidates": ranked,
        }
