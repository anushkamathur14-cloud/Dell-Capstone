"""Treatment bundle generation from world specification."""

from __future__ import annotations

import json
from datetime import datetime

import pandas as pd

from synthetic_env.world_spec.models import ArmSpec, WorldSpec


def _is_valid(arm: ArmSpec) -> bool:
    if arm.promotion_intensity == "aggressive" and arm.ui_friction > 0.7:
        return False
    if arm.matchmaking_delay_sec > 35 and arm.difficulty_shift > 0.2:
        return False
    if arm.reward_rate > 1.8 and arm.progression_speed > 1.6:
        return False
    return True


def generate_experiment_tables(spec: WorldSpec, experiment_id: str = "exp_0001") -> tuple[pd.DataFrame, pd.DataFrame]:
    now = datetime.utcnow()
    experiments = pd.DataFrame(
        [
            {
                "experiment_id": experiment_id,
                "objective": spec.meta.get("default_objective", "day7_retention"),
                "start_date": now,
                "end_date": None,
                "status": "active",
                "traffic_split": json.dumps({"control": 0.4, "fast_progression": 0.3, "guided_onboarding": 0.3}),
                "notes": "Synthetic benchmark experiment",
            }
        ]
    )

    arms_rows = []
    for arm_id, arm in spec.example_arms.items():
        if _is_valid(arm):
            arm_payload = arm.model_dump()
            constraints_tag = arm_payload.pop("constraints_tag")
            arms_rows.append(
                {
                    "experiment_id": experiment_id,
                    "arm_id": arm_id,
                    "treatment_description": f"{arm_id} synthetic bundle",
                    "structured_parameters_json": json.dumps(arm_payload),
                    "treatment_type": "configured_bundle",
                    "constraints_tag": constraints_tag,
                }
            )

    return experiments, pd.DataFrame(arms_rows)
