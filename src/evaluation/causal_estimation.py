"""Deterministic causal-style estimates from per-arm metrics summaries."""

from __future__ import annotations

import math
from typing import Any, Optional

from src.data.models import MetricsSummary

CONTROL_ARM_IDS = ("control", "baseline")


def _metric_value(row: MetricsSummary, metric: str) -> Optional[float]:
    value = getattr(row, metric, None)
    if value is None:
        return None
    return float(value)


def pick_control_arm(metrics: list[MetricsSummary]) -> MetricsSummary:
    for row in metrics:
        if row.arm_id.lower() in CONTROL_ARM_IDS:
            return row
    return metrics[0]


def pick_best_variant(metrics: list[MetricsSummary], control: MetricsSummary, metric: str) -> MetricsSummary:
    variants = [row for row in metrics if row.arm_id != control.arm_id]
    if not variants:
        return control

    def sort_key(row: MetricsSummary) -> float:
        return _metric_value(row, metric) or 0.0

    return max(variants, key=sort_key)


def _stderr(row: MetricsSummary, metric: str) -> float:
    sample_size = max(int(row.sample_size), 1)
    variance = row.variance
    if variance is not None and variance > 0:
        return math.sqrt(variance / sample_size)
    if row.confidence_interval and len(row.confidence_interval) == 2:
        half_width = abs(row.confidence_interval[1] - row.confidence_interval[0]) / 2.0
        return half_width / 1.96 if half_width > 0 else 0.05
    return 0.05


def estimate_causal_effects(
    metrics: list[MetricsSummary],
    objective: str = "retention",
) -> dict[str, Any]:
    """Difference-in-means style lift with normalized uncertainty (no LLM)."""
    metric = "retention" if "retention" in objective.lower() else "conversion"
    if not metrics:
        return {
            "estimated_lift": 0.0,
            "uncertainty": 1.0,
            "segment_effects": {},
            "ranked_directions": ["collect more arm-level metrics before evaluation"],
            "estimator": "none",
            "control_arm_id": None,
            "variant_arm_id": None,
            "_stub": False,
        }

    control = pick_control_arm(metrics)
    variant = pick_best_variant(metrics, control, metric)
    control_value = _metric_value(control, metric) or 0.0
    variant_value = _metric_value(variant, metric) or 0.0
    estimated_lift = variant_value - control_value

    pooled_stderr = math.sqrt(_stderr(control, metric) ** 2 + _stderr(variant, metric) ** 2)
    uncertainty = min(1.0, max(0.01, pooled_stderr * 4.0))

    direction = f"scale {variant.arm_id} patterns to improve {metric}"
    if estimated_lift <= 0:
        direction = f"iterate on {control.arm_id} baseline; current variants do not beat control on {metric}"

    return {
        "estimated_lift": round(estimated_lift, 6),
        "placeholder_lift": round(estimated_lift, 6),
        "uncertainty": round(uncertainty, 6),
        "segment_effects": {},
        "ranked_directions": [direction],
        "estimator": "difference_in_means_v1",
        "control_arm_id": control.arm_id,
        "variant_arm_id": variant.arm_id,
        "evaluation_metric": metric,
        "_stub": False,
    }
