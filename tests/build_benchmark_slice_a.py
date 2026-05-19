"""Build tiny fixture parquets used by test_retrieval.py.

Schemas mirror the calibrated benchmark exactly so the acceptance test
exercises the same code paths as production runs.

Run once to (re)generate the files; the parquets are checked into
`tests/fixtures/benchmark_slice_a/` so CI does not depend on this script.

    python tests/fixtures/build_benchmark_slice_a.py
"""

from __future__ import annotations

import json
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

FIXTURE_DIR = Path(__file__).parent / "benchmark_slice_a"

EXP_ID = "exp_fixture_001"


def _write(name: str, rows: list[dict]) -> None:
    FIXTURE_DIR.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist(rows)
    pq.write_table(table, FIXTURE_DIR / name)


def build() -> None:
    _write(
        "experiments.parquet",
        [
            {
                "experiment_id": EXP_ID,
                "objective": "day7_retention",
                "start_date": None,
                "end_date": None,
                "status": "active",
                "traffic_split": json.dumps(
                    {"control": 0.5, "fast_progression": 0.5}
                ),
                "notes": "Fixture for Slice A acceptance test",
            },
        ],
    )

    _write(
        "arms.parquet",
        [
            {
                "experiment_id": EXP_ID,
                "arm_id": "control",
                "treatment_description": "Baseline configuration",
                "structured_parameters_json": json.dumps(
                    {"difficulty_shift": 0.0, "reward_rate": 1.0}
                ),
                "treatment_type": "configured_bundle",
                "constraints_tag": "safe",
            },
            {
                "experiment_id": EXP_ID,
                "arm_id": "fast_progression",
                "treatment_description": "Faster level progression",
                "structured_parameters_json": json.dumps(
                    {"difficulty_shift": -0.2, "reward_rate": 1.15}
                ),
                "treatment_type": "configured_bundle",
                "constraints_tag": "safe",
            },
        ],
    )

    _write(
        "metrics_summary.parquet",
        [
            {
                "experiment_id": EXP_ID,
                "arm_id": "control",
                "sample_size": 1000,
                "conversion": 0.58,
                "retention": 0.41,
                "engagement": 49.2,
                "revenue_proxy": 1.05,
                "variance": 0.24,
                "confidence_interval": [0.39, 0.43],
            },
            {
                "experiment_id": EXP_ID,
                "arm_id": "fast_progression",
                "sample_size": 1000,
                "conversion": 0.62,
                "retention": 0.47,
                "engagement": 51.8,
                "revenue_proxy": 1.12,
                "variance": 0.22,
                "confidence_interval": [0.45, 0.49],
            },
        ],
    )

    _write(
        "observations.parquet",
        [
            {
                "entity_id": f"user_{i:07d}",
                "experiment_id": EXP_ID,
                "arm_id": "control" if i % 2 == 0 else "fast_progression",
                "timestamp": "2026-04-26T16:09:08",
                "context_features_json": json.dumps({"segment_id": "casual"}),
                "outcomes_json": json.dumps({"day7_retention": i % 2}),
                "exposure_flag": True,
                "segment_id": "casual",
                "day1_retention": 1,
                "day7_retention": i % 2,
                "engagement_time": 60.0 + i,
                "interaction_count": 10 + i,
                "monetization_proxy": 0.5,
                "satisfaction_proxy": 0.6,
            }
            for i in range(6)
        ],
    )

    _write(
        "experiment_memory.parquet",
        [
            {
                "experiment_id": EXP_ID,
                "summary_text": "Top arm by day7 retention: fast_progression.",
                "lessons_learned": "Heterogeneous effects observed across segments.",
                "winning_patterns": "fast_progression",
                "failed_patterns": "control",
                "analyst_notes": "Fixture memory row.",
            },
        ],
    )

    print(f"Wrote fixture parquets to {FIXTURE_DIR}")


if __name__ == "__main__":
    build()
