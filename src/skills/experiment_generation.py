"""Experiment generation skill stub."""

from src.data.models import RecommendationCandidate


class ExperimentGenerationSkill:
    def run(self, context: dict, evaluation: dict) -> list[RecommendationCandidate]:
        experiment_id = context["experiment"].experiment_id
        baseline_metric = context["metrics"][0] if context["metrics"] else None
        return [
            RecommendationCandidate(
                candidate_name=f"{experiment_id}-candidate-1",
                parameter_changes={"onboarding_copy": "value_prop_v2"},
                rationale="Lift first-session conversion for new users.",
                expected_tradeoff="May reduce exploration depth.",
                target_segment="new_users",
                implementation_notes="Roll out with capped traffic first.",
                signal_from_eval=evaluation["ranked_directions"][0],
                metric_stub={
                    "retention": baseline_metric.retention if baseline_metric else None,
                    "variance": baseline_metric.variance if baseline_metric else None,
                },
            )
        ]
