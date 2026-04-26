"""Simulate canonical observations and metrics from users and treatment bundles."""

from __future__ import annotations

import json
from datetime import datetime

import numpy as np
import pandas as pd


def _assign_arms(users: pd.DataFrame, arm_ids: list[str], seed: int) -> np.ndarray:
    rng = np.random.default_rng(seed)
    return rng.choice(arm_ids, size=len(users), p=np.repeat(1 / len(arm_ids), len(arm_ids)))


def _score_outcomes(df: pd.DataFrame, seed: int) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    is_new = (df["lifecycle_stage"] == "new").astype(float)
    is_core = (df["segment_id"] == "core").astype(float)

    arm_effect = {
        "control": {"difficulty_shift": 0.0, "reward_rate": 1.0, "ui_friction": 0.35, "progression_speed": 1.0},
        "fast_progression": {"difficulty_shift": -0.05, "reward_rate": 1.4, "ui_friction": 0.4, "progression_speed": 1.4},
        "high_challenge": {"difficulty_shift": 0.2, "reward_rate": 0.9, "ui_friction": 0.25, "progression_speed": 0.9},
        "guided_onboarding": {"difficulty_shift": -0.15, "reward_rate": 1.1, "ui_friction": 0.2, "progression_speed": 0.9},
    }

    params = df["arm_id"].map(arm_effect)
    difficulty_shift = params.map(lambda p: p["difficulty_shift"])
    reward_rate = params.map(lambda p: p["reward_rate"])
    ui_friction = params.map(lambda p: p["ui_friction"])
    progression_speed = params.map(lambda p: p["progression_speed"])

    interaction_term = (df["baseline_skill"] - 0.5) * difficulty_shift
    friction_penalty = ui_friction * (1 - df["friction_tolerance"])
    delayed_tradeoff = np.maximum(0, reward_rate - 1.25) * 0.15

    latent_engagement = (
        0.8 * df["engagement_propensity"]
        + 0.2 * df["recent_activity_score"]
        + 0.25 * reward_rate
        + 0.15 * progression_speed
        - 0.35 * friction_penalty
        + 0.2 * interaction_term
        + rng.normal(0, 0.12, len(df))
    )

    engagement_time = np.clip(22 + 35 * latent_engagement, 1, None)
    interaction_count = np.clip(np.round(3 + engagement_time / 4 + rng.normal(0, 2, len(df))), 0, None).astype(int)

    d1_logit = (
        -0.2
        + 1.2 * latent_engagement
        - 0.7 * df["churn_risk"]
        + 0.35 * is_new * (df["arm_id"] == "guided_onboarding").astype(float)
    )
    d1_prob = 1 / (1 + np.exp(-d1_logit))
    day1_retention = rng.binomial(1, np.clip(d1_prob, 0.01, 0.99), len(df))

    d7_logit = (
        -0.4
        + 1.1 * latent_engagement
        + 0.15 * is_core * (df["arm_id"] == "high_challenge").astype(float)
        - 0.9 * delayed_tradeoff
        - 0.35 * friction_penalty
    )
    d7_prob = 1 / (1 + np.exp(-d7_logit))
    day7_retention = rng.binomial(1, np.clip(d7_prob, 0.01, 0.99), len(df))

    monetization_proxy = np.clip(
        0.3
        + 0.7 * df["spend_propensity"]
        + 0.15 * np.log1p(engagement_time)
        + 0.08 * (df["arm_id"] == "fast_progression").astype(float)
        + rng.normal(0, 0.08, len(df)),
        0,
        None,
    )

    satisfaction_proxy = np.clip(
        0.7 + 0.25 * day1_retention - 0.4 * friction_penalty - 0.15 * delayed_tradeoff + rng.normal(0, 0.06, len(df)),
        0,
        1,
    )

    df = df.copy()
    df["engagement_time"] = engagement_time
    df["interaction_count"] = interaction_count
    df["day1_retention"] = day1_retention
    df["day7_retention"] = day7_retention
    df["monetization_proxy"] = monetization_proxy
    df["satisfaction_proxy"] = satisfaction_proxy
    return df


def simulate_observations(users: pd.DataFrame, experiment_id: str, arm_ids: list[str], seed: int = 42) -> pd.DataFrame:
    assigned = users.copy()
    assigned["arm_id"] = _assign_arms(assigned, arm_ids=arm_ids, seed=seed)
    scored = _score_outcomes(assigned, seed=seed)

    now = datetime.utcnow().isoformat()
    obs_rows = []
    for row in scored.itertuples(index=False):
        context = {
            "segment_id": row.segment_id,
            "acquisition_source": row.acquisition_source,
            "baseline_skill": float(row.baseline_skill),
            "engagement_propensity": float(row.engagement_propensity),
            "spend_propensity": float(row.spend_propensity),
            "friction_tolerance": float(row.friction_tolerance),
            "churn_risk": float(row.churn_risk),
        }
        outcomes = {
            "day1_retention": int(row.day1_retention),
            "day7_retention": int(row.day7_retention),
            "engagement_time": float(row.engagement_time),
            "interaction_count": int(row.interaction_count),
            "monetization_proxy": float(row.monetization_proxy),
            "satisfaction_proxy": float(row.satisfaction_proxy),
        }
        obs_rows.append(
            {
                "entity_id": row.entity_id,
                "experiment_id": experiment_id,
                "arm_id": row.arm_id,
                "timestamp": now,
                "context_features_json": json.dumps(context),
                "outcomes_json": json.dumps(outcomes),
                "exposure_flag": True,
                "segment_id": row.segment_id,
                "day1_retention": outcomes["day1_retention"],
                "day7_retention": outcomes["day7_retention"],
                "engagement_time": outcomes["engagement_time"],
                "interaction_count": outcomes["interaction_count"],
                "monetization_proxy": outcomes["monetization_proxy"],
                "satisfaction_proxy": outcomes["satisfaction_proxy"],
            }
        )

    return pd.DataFrame(obs_rows)


def summarize_metrics(observations: pd.DataFrame, experiment_id: str) -> pd.DataFrame:
    grouped = observations.groupby("arm_id", as_index=False).agg(
        sample_size=("entity_id", "count"),
        conversion=("day1_retention", "mean"),
        retention=("day7_retention", "mean"),
        engagement=("engagement_time", "mean"),
        revenue_proxy=("monetization_proxy", "mean"),
        variance=("day7_retention", "var"),
    )
    grouped["variance"] = grouped["variance"].fillna(0.0)
    grouped["confidence_interval"] = grouped.apply(
        lambda row: [
            max(0.0, row["retention"] - 1.96 * np.sqrt(max(row["variance"], 1e-6) / max(row["sample_size"], 1))),
            min(1.0, row["retention"] + 1.96 * np.sqrt(max(row["variance"], 1e-6) / max(row["sample_size"], 1))),
        ],
        axis=1,
    )
    grouped.insert(0, "experiment_id", experiment_id)
    return grouped


def create_experiment_memory(metrics_summary: pd.DataFrame, experiment_id: str) -> pd.DataFrame:
    top = metrics_summary.sort_values("retention", ascending=False).iloc[0]
    bottom = metrics_summary.sort_values("retention", ascending=True).iloc[0]
    return pd.DataFrame(
        [
            {
                "experiment_id": experiment_id,
                "summary_text": f"Top arm by day7 retention: {top['arm_id']}.",
                "lessons_learned": "Heterogeneous effects observed across segments.",
                "winning_patterns": f"{top['arm_id']}",
                "failed_patterns": f"{bottom['arm_id']}",
                "analyst_notes": "Synthetic summary generated by deterministic simulator.",
            }
        ]
    )
