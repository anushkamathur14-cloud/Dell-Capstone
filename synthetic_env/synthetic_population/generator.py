"""Generate synthetic populations with interpretable segment mixtures."""

from __future__ import annotations

import numpy as np
import pandas as pd

from synthetic_env.world_spec.models import WorldSpec


ACQ_SOURCES = ["organic", "paid", "referral", "cross_sell"]
LIFECYCLE = ["new", "maturing", "established", "at_risk"]


def generate_population(spec: WorldSpec, n_users: int = 5000, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    seg_ids = [segment.id for segment in spec.segments]
    seg_probs = np.array([segment.share for segment in spec.segments], dtype=float)
    seg_probs = seg_probs / seg_probs.sum()

    segment_assignment = rng.choice(seg_ids, size=n_users, p=seg_probs)
    users = pd.DataFrame(
        {
            "entity_id": [f"user_{i:07d}" for i in range(n_users)],
            "segment_id": segment_assignment,
            "acquisition_source": rng.choice(ACQ_SOURCES, size=n_users, p=[0.45, 0.25, 0.2, 0.1]),
            "lifecycle_stage": rng.choice(LIFECYCLE, size=n_users, p=[0.3, 0.3, 0.25, 0.15]),
            "recent_sessions_7d": rng.integers(0, 15, size=n_users),
        }
    )

    for segment in spec.segments:
        mask = users["segment_id"] == segment.id
        size = int(mask.sum())
        users.loc[mask, "baseline_skill"] = np.clip(rng.normal(segment.baseline_skill_mean, 0.15, size), 0, 1)
        users.loc[mask, "engagement_propensity"] = np.clip(
            rng.normal(segment.engagement_propensity_mean, 0.12, size), 0, 1
        )
        users.loc[mask, "spend_propensity"] = np.clip(rng.normal(segment.spend_propensity_mean, 0.15, size), 0, 1)
        users.loc[mask, "friction_tolerance"] = np.clip(
            rng.normal(segment.friction_tolerance_mean, 0.14, size), 0, 1
        )

    users["recent_activity_score"] = np.clip(
        0.45 * users["engagement_propensity"] + 0.55 * (users["recent_sessions_7d"] / 14.0) + rng.normal(0, 0.07, n_users),
        0,
        1,
    )
    users["churn_risk"] = np.clip(
        0.65 - 0.5 * users["recent_activity_score"] + 0.25 * (1 - users["friction_tolerance"]) + rng.normal(0, 0.05, n_users),
        0,
        1,
    )

    return users
