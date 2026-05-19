"""Recommendation skill stub."""

from src.data.models import RecommendationCandidate


class RecommendationSkill:
    def run(
        self,
        candidates: list[RecommendationCandidate | dict],
        evaluation: dict,
    ) -> dict:
        ranked = []
        uncertainty = float(evaluation.get("uncertainty", 0.2))
        for candidate in candidates:
            candidate_data = (
                candidate.model_dump()
                if isinstance(candidate, RecommendationCandidate)
                else dict(candidate)
            )
            metric_stub = candidate_data.get("metric_stub") or {}
            retention = metric_stub.get("retention") if metric_stub.get("retention") is not None else 0.0
            variance = metric_stub.get("variance") if metric_stub.get("variance") is not None else 0.0
            score = retention - (0.2 * variance) + 0.2 * (1 - uncertainty)
            ranked.append({**candidate_data, "score": round(score, 3)})

        ranked.sort(key=lambda c: c["score"], reverse=True)

        return {
            "top_recommendation": ranked[0] if ranked else None,
            "ranked_candidates": ranked,
        }
