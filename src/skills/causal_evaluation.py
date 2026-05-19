"""Causal evaluation skill backed by deterministic estimators."""

from __future__ import annotations

from src.data.models import MetricsSummary
from src.evaluation.causal_estimation import estimate_causal_effects


class CausalEvaluationSkill:
    def run(self, context: dict) -> dict:
        metrics: list[MetricsSummary] = context.get("metrics") or []
        objective = context.get("experiment").objective if context.get("experiment") else "retention"
        return estimate_causal_effects(metrics=metrics, objective=objective)
