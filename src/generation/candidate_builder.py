"""Build and validate RecommendationCandidate rows from context + evaluation."""

from __future__ import annotations

from typing import Any

from src.data.models import MetricsSummary, RecommendationCandidate
from src.evaluation.causal_estimation import pick_best_variant, pick_control_arm


def build_candidates_from_context(context: dict, evaluation: dict) -> list[RecommendationCandidate]:
    experiment_id = context["experiment"].experiment_id
    metrics: list[MetricsSummary] = context.get("metrics") or []
    objective = context.get("experiment").objective
    metric_key = evaluation.get("evaluation_metric") or (
        "retention" if "retention" in objective.lower() else "conversion"
    )

    if metrics:
        control = pick_control_arm(metrics)
        best = pick_best_variant(metrics, control, metric_key)
        base_value = getattr(best, metric_key, None) or getattr(control, metric_key, None) or 0.4
        base_variance = best.variance if best.variance is not None else control.variance or 0.02
        base_params = {}
        for arm in context.get("arms") or []:
            if arm.arm_id == best.arm_id:
                base_params = dict(arm.structured_parameters_json)
                break
    else:
        base_value = 0.4
        base_variance = 0.02
        base_params = {"ux_flow": "v1"}

    direction = (evaluation.get("ranked_directions") or ["improve core KPI"])[0]
    lift = float(evaluation.get("estimated_lift") or 0.0)

    conservative_params = {**base_params, "iteration": "conservative_v1"}
    aggressive_params = {
        **base_params,
        "iteration": "aggressive_v1",
        "reward_rate": min(2.0, float(base_params.get("reward_rate", 1.0)) + 0.15),
    }

    candidates = [
        RecommendationCandidate(
            candidate_name=f"{experiment_id}-candidate-1",
            parameter_changes=conservative_params,
            rationale=f"Conservative follow-up aligned with evaluation signal (lift={lift:.4f}).",
            expected_tradeoff="Lower variance, smaller expected upside.",
            target_segment="all_users",
            implementation_notes="Cap traffic at 15% until validation passes.",
            signal_from_eval=direction,
            metric_stub={
                metric_key: min(1.0, base_value + max(0.0, lift) * 0.5),
                "variance": base_variance,
            },
        ),
        RecommendationCandidate(
            candidate_name=f"{experiment_id}-candidate-2",
            parameter_changes=aggressive_params,
            rationale=f"Aggressive variant building on best arm patterns ({direction}).",
            expected_tradeoff="Higher reward cost and implementation complexity.",
            target_segment="new_users",
            implementation_notes="Requires validation go/caution; monitor day-7 readout.",
            signal_from_eval=direction,
            metric_stub={
                metric_key: min(1.0, base_value + max(0.02, lift) + 0.04),
                "variance": base_variance,
            },
        ),
    ]

    validated: list[RecommendationCandidate] = []
    for candidate in candidates:
        validated.append(RecommendationCandidate.model_validate(candidate.model_dump()))
    return validated
