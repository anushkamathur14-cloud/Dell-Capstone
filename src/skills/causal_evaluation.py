"""Causal evaluation skill — Slice B.

Output schema v1: stable contract for orchestrator and recommendation skill.
"""

from __future__ import annotations
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


class CausalEvaluationSkill:
    def run(self, context: dict) -> dict:
        return {
            "schema_version": "1.0",
            "arms_evaluated": [],
            "lift_estimates": {},
            "uncertainty": {},
            "segment_effects": {},
            "ranked_directions": [],
            "notes": "",
        }