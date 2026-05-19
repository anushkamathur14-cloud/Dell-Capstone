"""Causal evaluation skill: programmatic estimator + design + sandbox analysis."""

from __future__ import annotations

import json
import math
from typing import Any, Optional

from src.data.models import MetricsSummary
from src.evaluation.causal_estimation import estimate_causal_effects
from src.sandbox.daytona_runner import run_python_in_sandbox


class CausalEvaluationSkill:
    def run_programmatic(self, context: dict) -> dict:
        """Default path when sandbox is off or fails."""
        metrics: list[MetricsSummary] = context.get("metrics") or []
        objective = context.get("experiment").objective if context.get("experiment") else "retention"
        return estimate_causal_effects(metrics=metrics, objective=objective)

    def run(self, context: dict) -> dict:
        return self.run_programmatic(context)

    def design_experiment(self, context: dict, evaluation: Optional[dict] = None) -> dict[str, Any]:
        """Propose arms, sample sizes, and primary metric for a follow-up experiment."""
        metrics: list[MetricsSummary] = context.get("metrics") or []
        objective = context.get("experiment").objective if context.get("experiment") else "day7_retention"
        metric = (evaluation or {}).get("evaluation_metric") or (
            "retention" if "retention" in objective.lower() else "conversion"
        )
        per_arm_n = []
        for row in metrics:
            baseline_n = max(500, int(row.sample_size) if row.sample_size else 1000)
            per_arm_n.append({"arm_id": row.arm_id, "recommended_sample_size": baseline_n})

        if not per_arm_n:
            per_arm_n = [
                {"arm_id": "control", "recommended_sample_size": 2000},
                {"arm_id": "variant_a", "recommended_sample_size": 2000},
            ]

        return {
            "design_id": f"{context['experiment'].experiment_id}-followup",
            "primary_metric": metric,
            "arms": per_arm_n,
            "randomization": "equal_split",
            "duration_days": 14,
            "hypothesis": (evaluation or {}).get("ranked_directions", ["Improve primary KPI"])[0],
            "power_target": 0.8,
            "alpha": 0.05,
        }

    def run_sandbox_analysis(self, context: dict, evaluation: dict) -> dict[str, Any]:
        """Extended analysis in Daytona/local sandbox; falls back to programmatic only on failure."""
        metrics_payload = [
            {
                "arm_id": m.arm_id,
                "sample_size": m.sample_size,
                "retention": m.retention,
                "conversion": m.conversion,
                "variance": m.variance,
            }
            for m in (context.get("metrics") or [])
        ]
        code = """
import json
import math

import numpy as np
import pandas as pd

df = pd.DataFrame(payload["metrics"])
result = {"status": "ok", "tests": []}
if len(df) >= 2 and "retention" in df.columns:
    ctrl = df[df["arm_id"].str.contains("control|baseline", case=False, regex=True)]
    if ctrl.empty:
        ctrl = df.iloc[[0]]
    var = df[~df.index.isin(ctrl.index)]
    if var.empty:
        var = df.iloc[[1]]
    c_mean = float(ctrl["retention"].mean())
    v_mean = float(var["retention"].mean())
    diff = v_mean - c_mean
    se = math.sqrt(
        float(ctrl["variance"].fillna(0.01).mean()) / max(int(ctrl["sample_size"].mean()), 1)
        + float(var["variance"].fillna(0.01).mean()) / max(int(var["sample_size"].mean()), 1)
    )
    z = diff / se if se > 0 else 0.0
    result["tests"].append({
        "name": "two_arm_z_approx",
        "lift": diff,
        "z_score": z,
        "significant_95": abs(z) > 1.96,
    })
    result["segment_note"] = "sandbox_extended"
else:
    result["note"] = "insufficient arms for sandbox test"
"""
        sandbox_out = run_python_in_sandbox(
            code=code,
            payload={"metrics": metrics_payload, "evaluation": evaluation},
        )
        programmatic = self.run_programmatic(context)
        if sandbox_out.get("status") == "ok" and sandbox_out.get("result"):
            programmatic["sandbox_analysis"] = sandbox_out["result"]
            programmatic["analysis_source"] = sandbox_out.get("source", "sandbox")
        else:
            programmatic["sandbox_analysis"] = {
                "status": "fallback",
                "reason": sandbox_out.get("error") or sandbox_out.get("reason", "sandbox unavailable"),
            }
            programmatic["analysis_source"] = "programmatic_only"
        return programmatic
