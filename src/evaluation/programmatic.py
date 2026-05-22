"""Deterministic causal evaluation (no LLM)."""

from __future__ import annotations

from typing import Any


def run_programmatic_causal(context: dict[str, Any]) -> dict[str, Any]:
    baseline = context["metrics"][0]
    placeholder_lift = (baseline.conversion or 0.0) * 0.05
    uncertainty = min(1.0, max(0.01, (baseline.variance or 0.1) ** 0.5))
    ranked_direction = "optimize onboarding messaging"
    if (baseline.retention or 0.0) < 0.5:
        ranked_direction = "reduce day-7 churn for early lifecycle users"
    return {
        "estimated_lift": placeholder_lift,
        "placeholder_lift": placeholder_lift,
        "uncertainty": uncertainty,
        "segment_effects": {},
        "ranked_directions": [ranked_direction],
    }
