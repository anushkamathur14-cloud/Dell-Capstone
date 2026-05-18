"""Experiment generation skill stub."""

from src.data.models import RecommendationCandidate


class ExperimentGenerationSkill:
    def run(self, context: dict, evaluation: dict) -> list[RecommendationCandidate]:
        experiment_id = context["experiment"].experiment_id
        baseline_metric = context["metrics"][0] if context["metrics"] else None
        base_retention = baseline_metric.retention if baseline_metric else 0.4
        base_variance = baseline_metric.variance if baseline_metric else 0.02
        direction = evaluation["ranked_directions"][0]
        return [
            RecommendationCandidate(
                candidate_name=f"{experiment_id}-candidate-1",
                parameter_changes={"onboarding_copy": "value_prop_v2"},
                rationale="Lift first-session conversion for new users.",
                expected_tradeoff="May reduce exploration depth.",
                target_segment="new_users",
                implementation_notes="Roll out with capped traffic first.",
                signal_from_eval=direction,
                metric_stub={"retention": base_retention, "variance": base_variance},
            ),
            RecommendationCandidate(
                candidate_name=f"{experiment_id}-candidate-2",
                parameter_changes={"onboarding_copy": "guided_walkthrough_v1", "reward_rate": 1.15},
                rationale="Improve day-7 retention via guided onboarding.",
                expected_tradeoff="Slightly higher reward cost per session.",
                target_segment="new_users",
                implementation_notes="Cap traffic at 20% until day-7 readout.",
                signal_from_eval=direction,
                metric_stub={
                    "retention": min(1.0, (base_retention or 0.0) + 0.08),
                    "variance": base_variance,
                },
            ),
        ]
