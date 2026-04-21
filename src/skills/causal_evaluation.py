"""Causal evaluation skill stub."""


class CausalEvaluationSkill:
    def run(self, context: dict) -> dict:
        baseline = context["metrics"][0]
        return {
            "estimated_lift": baseline.conversion * 0.05,
            "uncertainty": 0.1,
            "segment_effects": {},
            "ranked_directions": ["optimize onboarding messaging"],
        }
