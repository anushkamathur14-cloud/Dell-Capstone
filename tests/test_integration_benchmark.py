"""End-to-end orchestration on frozen benchmark (no LLM)."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.agent.orchestrator import AdaptiveExperimentationOrchestrator

BENCHMARK_DIR = Path("synthetic_env/benchmarks/generated_sanity_calibrated")
EXPERIMENT_ID = "exp_sanity_001_calibrated"


@pytest.mark.skipif(
    not (BENCHMARK_DIR / "experiments.parquet").exists(),
    reason="calibrated benchmark bundle not present",
)
def test_canonical_pipeline_on_calibrated_benchmark() -> None:
    result = AdaptiveExperimentationOrchestrator().run(
        objective="day7_retention",
        experiment_id=EXPERIMENT_ID,
    )

    assert result.schema_version == "v1.0"
    assert result.validation_report["decision"] in {"go", "caution"}
    assert result.validation_report.get("benchmark_loaded") is True
    assert len(result.metrics) >= 4
    assert len(result.candidates) >= 4
    assert result.evaluation.get("ranked_directions")
    assert result.evaluation.get("segment_effects")
    top = result.recommendation["top_recommendation"]
    assert top is not None
    assert top["score"] > 0
