"""Post-experiment statistical analysis skill (runs after experiment completes)."""

from __future__ import annotations

from typing import Any, Optional

from src.data.models import StatisticalAnalysisReport
from src.evaluation.causal_estimation import estimate_causal_effects
from src.sandbox.daytona_runner import run_python_in_sandbox


class StatisticalAnalysisSkill:
    """Programmatic + optional sandbox deep-dive when status is completed."""

    def run(
        self,
        context: dict[str, Any],
        evaluation: Optional[dict[str, Any]] = None,
        validation_report: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        experiment = context["experiment"]
        metrics = context.get("metrics") or []
        objective = experiment.objective

        programmatic = estimate_causal_effects(metrics=metrics, objective=objective)
        arm_table = [
            {
                "arm_id": m.arm_id,
                "sample_size": m.sample_size,
                "retention": m.retention,
                "conversion": m.conversion,
                "variance": m.variance,
                "confidence_interval": m.confidence_interval,
            }
            for m in metrics
        ]

        summary_lines = [
            f"Experiment {experiment.experiment_id} ({experiment.status}): post-hoc statistical review.",
            f"Primary programmatic lift: {programmatic.get('estimated_lift')}",
            f"Uncertainty: {programmatic.get('uncertainty')}",
        ]
        if validation_report:
            summary_lines.append(f"Validation decision at run time: {validation_report.get('decision')}")

        sandbox_result: dict[str, Any] = {"status": "skipped", "reason": "not_completed"}
        if experiment.status.lower() in {"completed", "active", "done"}:
            code = """
import json
import math

import numpy as np
import pandas as pd

df = pd.DataFrame(payload["arm_table"])
out = {"tests": [], "descriptives": df.to_dict(orient="records")}
if len(df) >= 2 and df["retention"].notna().sum() >= 2:
    arms = df.groupby("arm_id")["retention"].mean()
    if len(arms) >= 2:
        diff = float(arms.max() - arms.min())
        out["tests"].append({"name": "arm_mean_spread", "lift_spread": diff})
    out["status"] = "ok"
else:
    out["status"] = "insufficient_data"
result = out
"""
            sandbox_result = run_python_in_sandbox(
                code=code,
                payload={"arm_table": arm_table, "evaluation": evaluation or programmatic},
            )

        report = StatisticalAnalysisReport(
            experiment_id=experiment.experiment_id,
            experiment_status=experiment.status,
            programmatic_summary="\n".join(summary_lines),
            programmatic_results=programmatic,
            arm_level_table=arm_table,
            sandbox_analysis=sandbox_result.get("result") or sandbox_result,
            analysis_source=sandbox_result.get("source", "programmatic"),
            evaluation_snapshot=evaluation or {},
        )
        return report.model_dump()
