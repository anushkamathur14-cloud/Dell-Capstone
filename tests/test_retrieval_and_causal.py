"""Tests for workstream A (retrieval) and C (causal evaluation)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.evaluation.causal_estimation import estimate_causal_effects
from src.retrieval.benchmark_context import load_context_from_benchmark
from src.skills.causal_evaluation import CausalEvaluationSkill
from src.skills.retrieval import RetrievalSkill
from src.data.models import MetricsSummary


def test_causal_evaluation_difference_in_means() -> None:
    metrics = [
        MetricsSummary(
            experiment_id="exp_test",
            arm_id="control",
            sample_size=1000,
            retention=0.40,
            variance=0.02,
            confidence_interval=[0.38, 0.42],
        ),
        MetricsSummary(
            experiment_id="exp_test",
            arm_id="variant_a",
            sample_size=1000,
            retention=0.48,
            variance=0.02,
            confidence_interval=[0.46, 0.50],
        ),
    ]
    result = estimate_causal_effects(metrics=metrics, objective="day7_retention")
    assert result["_stub"] is False
    assert result["estimator"] == "difference_in_means_v1"
    assert result["estimated_lift"] == pytest.approx(0.08, abs=1e-6)
    assert result["uncertainty"] > 0
    assert result["control_arm_id"] == "control"
    assert result["variant_arm_id"] == "variant_a"


def test_causal_evaluation_skill_from_context() -> None:
    context = RetrievalSkill().run(objective="improve_retention", experiment_id="exp_001")
    evaluation = CausalEvaluationSkill().run(context)
    assert evaluation["_stub"] is False
    assert evaluation["estimated_lift"] > 0


def test_retrieval_stub_when_no_benchmark(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("BENCHMARK_DATA_DIR", str(tmp_path))
    context = RetrievalSkill().run(objective="improve_retention", experiment_id="exp_001")
    assert context["data_source"] == "stub"
    assert len(context["metrics"]) >= 2


@pytest.mark.slow
def test_retrieval_loads_generated_benchmark(tmp_path: Path) -> None:
    from synthetic_env.pipeline import run_generation

    experiment_id = "exp_retrieval_test"
    run_generation(n_users=200, experiment_id=experiment_id, seed=11, output_dir=tmp_path)

    context = load_context_from_benchmark(
        benchmark_dir=tmp_path,
        experiment_id=experiment_id,
        objective="day7_retention",
    )
    assert context is not None
    assert context["data_source"] == "benchmark"
    assert context["experiment"].experiment_id == experiment_id
    assert len(context["arms"]) >= 2
    assert len(context["metrics"]) >= 2
