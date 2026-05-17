"""Causal evaluation skill

Output schema v1: stable contract for orchestrator and recommendation skill.
"""

from __future__ import annotations
from math import sqrt
from typing import Any


class EvaluationOutput:
    """Documents the required fields returned by CausalEvaluationSkill.run()."""

    schema_version: str                  # e.g. "1.0"
    arms_evaluated: list[str]            # arm_ids that were compared vs control
    lift_estimates: dict[str, dict]      # arm_id → {metric: lift_value}
    uncertainty: dict[str, float]        # arm_id → standard error of lift
    segment_effects: dict[str, Any]      # segment → arm → effect (stub ok for v1)
    ranked_directions: list[str]         # ordered arm_ids, best first
    notes: str                           # human-readable summary of what was found


# Weights for composite ranking score across metrics
_METRIC_WEIGHTS = {
    "conversion":    0.35,
    "retention":     0.35,
    "engagement":    0.15,
    "revenue_proxy": 0.15,
}


class CausalEvaluationSkill:
    def run(self, context: dict) -> dict:
        metrics = context["metrics"]

        # --- isolate control ---
        control = next((m for m in metrics if m.arm_id == "control"), None)
        if control is None:
            control = metrics[0]

        # --- compute lift and uncertainty for each non-control arm ---
        lift_estimates: dict[str, dict] = {}
        uncertainty: dict[str, float] = {}
        arms_evaluated: list[str] = []

        control_var = control.variance or 0.0

        for m in metrics:
            if m.arm_id == control.arm_id:
                continue

            arms_evaluated.append(m.arm_id)

            lift_estimates[m.arm_id] = {
                "conversion":    round((m.conversion    or 0) - (control.conversion    or 0), 4),
                "retention":     round((m.retention     or 0) - (control.retention     or 0), 4),
                "engagement":    round((m.engagement    or 0) - (control.engagement    or 0), 4),
                "revenue_proxy": round((m.revenue_proxy or 0) - (control.revenue_proxy or 0), 4),
            }

            arm_var = m.variance or 0.0
            uncertainty[m.arm_id] = round(sqrt(arm_var + control_var), 4)

        # --- rank arms by weighted composite score ---
        def composite_score(arm_id: str) -> float:
            lifts = lift_estimates[arm_id]
            return sum(lifts[metric] * weight for metric, weight in _METRIC_WEIGHTS.items())

        ranked_directions = sorted(arms_evaluated, key=composite_score, reverse=True)

        # --- build notes ---
        best = ranked_directions[0] if ranked_directions else "none"
        notes = (
            f"Lift computed vs control arm '{control.arm_id}' across {len(arms_evaluated)} treatment arms. "
            f"Top ranked arm: '{best}' by weighted composite score "
            f"(conversion 35%, retention 35%, engagement 15%, revenue 15%)."
        )

        return {
            "schema_version": "1.0",
            "arms_evaluated": arms_evaluated,
            "lift_estimates": lift_estimates,
            "uncertainty": uncertainty,
            "segment_effects": {},
            "ranked_directions": ranked_directions,
            "notes": notes,
        }

