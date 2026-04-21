"""Recommendation skill stub."""


class RecommendationSkill:
    def run(self, candidates: list[dict], evaluation: dict) -> dict:
        ranked = []
        for candidate in candidates:
            score = 0.5 + 0.3 * (1 - evaluation["uncertainty"]) + 0.2
            ranked.append({**candidate, "score": round(score, 3)})

        ranked.sort(key=lambda c: c["score"], reverse=True)

        return {
            "top_recommendation": ranked[0] if ranked else None,
            "ranked_candidates": ranked,
        }
