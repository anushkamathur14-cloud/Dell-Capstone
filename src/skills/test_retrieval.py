"""Slice A acceptance test.

Satisfies the minimum from Issue #1:
    > assert len(result["arms"]) >= 2 and at least one arm_id != "control"

Plus the shape / contract assertions required by
docs/implementation_plan_v1.md §4 Slice A "done means".
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.data.models import (
    ArmVariant,
    Experiment,
    ExperimentMemory,
    MetricsSummary,
)
from src.skills.retrieval import RetrievalError, RetrievalSkill, SCHEMA_VERSION

FIXTURE_DIR = Path(__file__).parent / "fixtures" / "benchmark_slice_a"
FIXTURE_EXP_ID = "exp_fixture_001"


@pytest.fixture(scope="module")
def fixture_dir() -> Path:
    """Path to the checked-in fixture parquets.

    Regenerate with:
        python tests/fixtures/build_benchmark_slice_a.py
    """
    if not (FIXTURE_DIR / "experiments.parquet").exists():
        pytest.skip(
            "Fixture parquets missing; run build_benchmark_slice_a.py first."
        )
    return FIXTURE_DIR


@pytest.fixture(scope="module")
def bundle(fixture_dir) -> dict:
    skill = RetrievalSkill(benchmark_dir=fixture_dir)
    return skill.run(
        objective="day7_retention", experiment_id=FIXTURE_EXP_ID
    )


# --- Issue #1 minimum -------------------------------------------------------


def test_loads_real_arms_not_hardcoded_stub(bundle):
    """Issue #1: assert >= 2 arms and a non-control arm.

    The pre-existing stub returned 1 hardcoded 'control' arm; this test
    fails against that stub and passes against the parquet adapter.
    """
    assert len(bundle["arms"]) >= 2
    non_control = [a for a in bundle["arms"] if a.arm_id != "control"]
    assert non_control, "Expected at least one non-control arm"


# --- Shape / contract -------------------------------------------------------


def test_bundle_has_canonical_keys(bundle):
    """Skills catalog mandates experiment, arms, memory, metrics."""
    required = {"experiment", "arms", "memory", "metrics"}
    assert required.issubset(bundle.keys())
    assert bundle["schema_version"] == SCHEMA_VERSION


def test_bundle_uses_team_models(bundle):
    """Output must use the Pydantic classes from src/data/models.py."""
    assert isinstance(bundle["experiment"], Experiment)
    assert all(isinstance(a, ArmVariant) for a in bundle["arms"])
    assert isinstance(bundle["memory"], ExperimentMemory)
    assert all(isinstance(m, MetricsSummary) for m in bundle["metrics"])


# --- Specific field behavior ------------------------------------------------


def test_arm_parameters_parsed_from_json(bundle):
    """structured_parameters_json must come out as a dict, not a string."""
    fast = next(
        a for a in bundle["arms"] if a.arm_id == "fast_progression"
    )
    assert isinstance(fast.structured_parameters_json, dict)
    assert "difficulty_shift" in fast.structured_parameters_json
    assert "reward_rate" in fast.structured_parameters_json


def test_control_arm_helper(bundle):
    """RetrievalSkill.is_control should identify the baseline arm."""
    controls = [a for a in bundle["arms"] if RetrievalSkill.is_control(a)]
    assert len(controls) == 1
    assert controls[0].arm_id == "control"


def test_traffic_split_parsed_from_json(bundle):
    """traffic_split is a JSON string in the parquet; must come out as dict."""
    split = bundle["experiment"].traffic_split
    assert isinstance(split, dict)
    assert "control" in split
    assert sum(split.values()) == pytest.approx(1.0, abs=0.01)


def test_memory_populated_from_parquet(bundle):
    """experiment_memory.parquet must flow into ExperimentMemory."""
    mem = bundle["memory"]
    assert mem.summary_text  # non-empty
    assert "fast_progression" in mem.winning_patterns


def test_memory_pattern_fields_are_lists(bundle):
    """winning_patterns / failed_patterns are list[str] in the model."""
    mem = bundle["memory"]
    assert isinstance(mem.winning_patterns, list)
    assert isinstance(mem.failed_patterns, list)
    assert isinstance(mem.lessons_learned, list)


def test_metrics_is_list_of_per_arm_rows(bundle):
    """Stub returned metrics as a list; we keep that shape."""
    assert isinstance(bundle["metrics"], list)
    assert len(bundle["metrics"]) >= 2
    arm_ids = {m.arm_id for m in bundle["metrics"]}
    assert "control" in arm_ids


# --- Failure modes ----------------------------------------------------------


def test_unknown_experiment_raises(fixture_dir):
    skill = RetrievalSkill(benchmark_dir=fixture_dir)
    with pytest.raises(RetrievalError, match="not found"):
        skill.run(
            objective="day7_retention", experiment_id="exp_does_not_exist"
        )


def test_missing_benchmark_dir_raises(tmp_path):
    # tmp_path exists but contains no parquets.
    skill = RetrievalSkill(benchmark_dir=tmp_path)
    with pytest.raises(RetrievalError, match="missing"):
        skill.run(objective="day7_retention", experiment_id=FIXTURE_EXP_ID)


def test_missing_benchmark_directory_raises(tmp_path):
    # Pointing at a non-existent directory altogether.
    missing = tmp_path / "does_not_exist"
    skill = RetrievalSkill(benchmark_dir=missing)
    with pytest.raises(RetrievalError, match="not found"):
        skill.run(objective="day7_retention", experiment_id=FIXTURE_EXP_ID)


# --- Memory absence ---------------------------------------------------------


def test_missing_memory_returns_empty_bundle(tmp_path, fixture_dir):
    """If experiment_memory.parquet has no row for the experiment, return
    an empty bundle with an explanatory analyst_notes; do not raise."""
    # Use the fixture but request an experiment_id absent from memory.
    # Easiest path: rebuild a minimal fixture without a memory row.
    # For simplicity we use monkeypatch-style: build a tiny set in tmp_path.
    import pyarrow as pa
    import pyarrow.parquet as pq
    import json

    exp_id = "exp_no_memory"
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "experiment_id": exp_id,
                    "objective": "day7_retention",
                    "start_date": None,
                    "end_date": None,
                    "status": "active",
                    "traffic_split": json.dumps(
                        {"control": 0.5, "treatment_a": 0.5}
                    ),
                    "notes": "fixture",
                }
            ]
        ),
        tmp_path / "experiments.parquet",
    )
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "experiment_id": exp_id,
                    "arm_id": "control",
                    "treatment_description": "Baseline",
                    "structured_parameters_json": json.dumps({}),
                    "treatment_type": "configured_bundle",
                    "constraints_tag": "safe",
                },
                {
                    "experiment_id": exp_id,
                    "arm_id": "treatment_a",
                    "treatment_description": "Test",
                    "structured_parameters_json": json.dumps(
                        {"k": 1.0}
                    ),
                    "treatment_type": "configured_bundle",
                    "constraints_tag": "safe",
                },
            ]
        ),
        tmp_path / "arms.parquet",
    )
    pq.write_table(
        pa.Table.from_pylist(
            [
                {
                    "experiment_id": exp_id,
                    "arm_id": "control",
                    "sample_size": 100,
                    "conversion": 0.5,
                    "retention": 0.4,
                    "engagement": 10.0,
                    "revenue_proxy": 1.0,
                    "variance": 0.1,
                    "confidence_interval": [0.3, 0.5],
                },
                {
                    "experiment_id": exp_id,
                    "arm_id": "treatment_a",
                    "sample_size": 100,
                    "conversion": 0.55,
                    "retention": 0.45,
                    "engagement": 11.0,
                    "revenue_proxy": 1.1,
                    "variance": 0.1,
                    "confidence_interval": [0.35, 0.55],
                },
            ]
        ),
        tmp_path / "metrics_summary.parquet",
    )
    # Empty observations and memory files so the reads don't crash.
    for fname in (
        "observations.parquet",
        "experiment_memory.parquet",
    ):
        pq.write_table(
            pa.Table.from_pylist([{"experiment_id": "OTHER"}]),
            tmp_path / fname,
        )

    skill = RetrievalSkill(benchmark_dir=tmp_path)
    bundle = skill.run(
        objective="day7_retention", experiment_id=exp_id
    )
    mem = bundle["memory"]
    assert mem.summary_text == ""
    assert mem.lessons_learned == []
    assert "No memory row found" in (mem.analyst_notes or "")
