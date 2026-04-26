"""Simple benchmark baselines for policy comparison."""

from __future__ import annotations

import pandas as pd


def random_baseline_score(metrics_summary: pd.DataFrame, metric: str = "retention") -> float:
    return float(metrics_summary[metric].mean())


def heuristic_baseline_score(metrics_summary: pd.DataFrame) -> float:
    scored = metrics_summary.copy()
    scored["heuristic_score"] = 0.7 * scored["retention"] + 0.2 * scored["engagement"] + 0.1 * scored["revenue_proxy"]
    return float(scored["heuristic_score"].max())


def agent_ready_hook(metrics_summary: pd.DataFrame) -> dict:
    return {
        "candidate_arms": metrics_summary[["arm_id", "retention", "engagement", "revenue_proxy"]]
        .sort_values("retention", ascending=False)
        .to_dict(orient="records")
    }
