"""Experiment generation skill stub."""


class ExperimentGenerationSkill:
    def run(self, context: dict, evaluation: dict) -> list[dict]:
        experiment_id = context["experiment"].experiment_id
        return [
            {
                "candidate_name": f"{experiment_id}-candidate-1",
                "parameter_changes": {"onboarding_copy": "value_prop_v2"},
                "rationale": "Lift first-session conversion for new users.",
                "expected_tradeoff": "May reduce exploration depth.",
                "target_segment": "new_users",
                "implementation_notes": "Roll out with capped traffic first.",
                "signal_from_eval": evaluation["ranked_directions"][0],
            }
        ]
