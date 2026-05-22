"""Deterministic causal evaluation from retrieval metrics (multi-arm)."""

from __future__ import annotations

from typing import Any


def run_programmatic_causal(context: dict[str, Any]) -> dict[str, Any]:
    metrics = context.get("metrics") or []
    if not metrics:
        return {
            "schema_version": "v1.0",
            "estimated_lift": 0.0,
            "placeholder_lift": 0.0,
            "uncertainty": 0.5,
            "segment_effects": {},
            "ranked_directions": ["insufficient_data"],
            "analysis_notes": "No metrics in context.",
        }

    by_arm = {m.arm_id: m for m in metrics}
    control = by_arm.get("control") or metrics[0]

    def _ret(m: Any) -> float:
        return float(m.retention or 0.0)

    ranked = sorted(metrics, key=_ret, reverse=True)
    best = ranked[0]
    control_ret = _ret(control)
    best_ret = _ret(best)
    lift = max(0.0, best_ret - control_ret)

    avg_variance = sum(float(m.variance or 0.1) for m in metrics) / len(metrics)
    uncertainty = min(1.0, max(0.01, avg_variance**0.5))

    segment_effects = {m.arm_id: round(_ret(m), 4) for m in metrics}
    ranked_directions = [
        f"prioritize_arm:{best.arm_id}",
        f"improve_vs_control:{best.arm_id}_vs_control",
    ]

    memory = context.get("memory")
    if memory and getattr(memory, "winning_patterns", None):
        wp = memory.winning_patterns[0] if memory.winning_patterns else best.arm_id
        if wp not in {d.split(":")[-1] for d in ranked_directions}:
            ranked_directions.append(f"memory_winner:{wp}")

    return {
        "schema_version": "v1.0",
        "estimated_lift": round(lift, 4),
        "placeholder_lift": round(lift, 4),
        "uncertainty": round(uncertainty, 4),
        "segment_effects": segment_effects,
        "ranked_directions": ranked_directions,
        "analysis_notes": (
            f"Programmatic compare: best={best.arm_id} retention={best_ret:.3f}, "
            f"control={control_ret:.3f}, lift={lift:.3f}."
        ),
    }
