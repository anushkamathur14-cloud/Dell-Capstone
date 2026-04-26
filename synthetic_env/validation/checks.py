"""Validation checks for structural, statistical, behavioral, and decision usefulness."""

from __future__ import annotations

import json

import numpy as np
import pandas as pd


REQUIRED_TABLE_COLUMNS = {
    "experiments": {"experiment_id", "objective", "status", "traffic_split"},
    "arms": {"experiment_id", "arm_id", "structured_parameters_json", "constraints_tag"},
    "observations": {"entity_id", "experiment_id", "arm_id", "exposure_flag", "outcomes_json"},
    "metrics_summary": {"experiment_id", "arm_id", "sample_size", "retention", "confidence_interval"},
}


def check_structural_fidelity(experiments: pd.DataFrame, arms: pd.DataFrame, observations: pd.DataFrame, metrics: pd.DataFrame) -> dict:
    checks = {
        "experiments_columns": REQUIRED_TABLE_COLUMNS["experiments"].issubset(set(experiments.columns)),
        "arms_columns": REQUIRED_TABLE_COLUMNS["arms"].issubset(set(arms.columns)),
        "observations_columns": REQUIRED_TABLE_COLUMNS["observations"].issubset(set(observations.columns)),
        "metrics_columns": REQUIRED_TABLE_COLUMNS["metrics_summary"].issubset(set(metrics.columns)),
        "observations_have_known_arms": set(observations["arm_id"]).issubset(set(arms["arm_id"])),
        "non_empty_tables": all(len(tbl) > 0 for tbl in [experiments, arms, observations, metrics]),
    }
    checks["pass"] = all(checks.values())
    return checks


def check_statistical_fidelity(population: pd.DataFrame, observations: pd.DataFrame) -> dict:
    seg_share = population["segment_id"].value_counts(normalize=True).to_dict()
    corr = observations[["engagement_time", "interaction_count", "monetization_proxy"]].corr(numeric_only=True)
    checks = {
        "segment_share": seg_share,
        "engagement_interaction_corr": float(corr.loc["engagement_time", "interaction_count"]),
        "engagement_monetization_corr": float(corr.loc["engagement_time", "monetization_proxy"]),
        "plausible_positive_corr": float(corr.loc["engagement_time", "interaction_count"]) > 0.25,
    }
    checks["pass"] = checks["plausible_positive_corr"]
    return checks


def check_behavioral_realism(observations: pd.DataFrame) -> dict:
    by_arm = observations.groupby("arm_id", as_index=False)[["day1_retention", "day7_retention", "satisfaction_proxy"]].mean()
    by_arm_segment = observations.groupby(["arm_id", "segment_id"], as_index=False)["day7_retention"].mean()

    heterogeneity = by_arm_segment.groupby("arm_id")["day7_retention"].std().fillna(0)
    has_heterogeneous_effects = bool((heterogeneity > 0.01).any())

    d1_vs_d7_gap = (by_arm["day1_retention"] - by_arm["day7_retention"]).abs().max()
    delayed_effect_present = bool(d1_vs_d7_gap > 0.03)

    return {
        "arm_level_means": by_arm.to_dict(orient="records"),
        "has_heterogeneous_effects": has_heterogeneous_effects,
        "delayed_effect_present": delayed_effect_present,
        "pass": has_heterogeneous_effects and delayed_effect_present,
    }


def check_decision_usefulness(metrics_summary: pd.DataFrame) -> dict:
    spread = metrics_summary["retention"].max() - metrics_summary["retention"].min()
    too_easy = spread < 0.01
    winner = metrics_summary.sort_values("retention", ascending=False).iloc[0]["arm_id"]
    return {
        "retention_spread": float(spread),
        "too_trivial": bool(too_easy),
        "best_arm": winner,
        "pass": not too_easy,
    }


def create_validation_report(
    population: pd.DataFrame,
    experiments: pd.DataFrame,
    arms: pd.DataFrame,
    observations: pd.DataFrame,
    metrics_summary: pd.DataFrame,
) -> dict:
    structural = check_structural_fidelity(experiments, arms, observations, metrics_summary)
    statistical = check_statistical_fidelity(population, observations)
    behavioral = check_behavioral_realism(observations)
    decision = check_decision_usefulness(metrics_summary)

    overall = all([structural["pass"], statistical["pass"], behavioral["pass"], decision["pass"]])

    return {
        "overall_pass": overall,
        "structural_fidelity": structural,
        "statistical_fidelity": statistical,
        "behavioral_realism": behavioral,
        "decision_usefulness": decision,
    }


def report_to_frame(report: dict) -> pd.DataFrame:
    rows = []
    for section, payload in report.items():
        if isinstance(payload, dict):
            rows.append({"section": section, "pass": payload.get("pass", None), "details": json.dumps(payload)})
    return pd.DataFrame(rows)
