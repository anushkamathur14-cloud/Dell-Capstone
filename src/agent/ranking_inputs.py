"""Build ranking candidate inputs from retrieval context (v1 canonical path).

Until Slice D plugs in structured proposals, recommendation consumes a stable list
derived from observable arms/metrics in the retrieval bundle.
"""

from __future__ import annotations

from typing import Any

from src.data.models import MetricsSummary


def ranking_candidates_from_context(context: dict[str, Any]) -> list[dict[str, Any]]:
    """One dict per metric row — sufficient for RecommendationSkill stubs."""

    metrics: list[MetricsSummary] = context.get("metrics", [])
    arms = context.get("arms", [])
    arm_params: dict[str, dict[str, Any]] = {}
    for arm in arms:
        arm_params[arm.arm_id] = dict(arm.structured_parameters_json or {})

    out: list[dict[str, Any]] = []
    for m in metrics:
        rid = str(m.arm_id)
        out.append(
            {
                "candidate_name": rid,
                "parameter_changes": arm_params.get(rid, {}),
                "rationale": "Ranking input derived from retrieval metrics (v1; no proposal layer).",
                "expected_tradeoff": "n/a",
                "target_segment": "aggregate",
                "implementation_notes": "Extend with experiment_generation_skill in Phase 2.",
                "signal_from_eval": "pending_eval_placeholder",
                "source": "retrieval_metrics",
                "metric_stub": {"retention": m.retention, "conversion": m.conversion},
            }
        )

    return out
