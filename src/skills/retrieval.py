"""Retrieval: benchmark parquets when available, else minimal stub."""

from __future__ import annotations

import os
from pathlib import Path

from src.data.benchmark_retrieval import load_benchmark_context
from src.data.models import ArmVariant, Experiment, ExperimentMemory, MetricsSummary


def _default_benchmark_dir() -> Path:
    return Path(
        os.getenv(
            "BENCHMARK_DATA_DIR",
            "synthetic_env/benchmarks/generated_sanity_calibrated",
        )
    )


class RetrievalSkill:
    def run(self, objective: str, experiment_id: str) -> dict:
        benchmark_dir = _default_benchmark_dir()
        loaded = load_benchmark_context(benchmark_dir, experiment_id, objective=objective)
        if loaded is not None:
            return loaded

        experiment = Experiment(
            experiment_id=experiment_id,
            objective=objective,
            status="completed",
            traffic_split={"control": 0.5, "variant_a": 0.5},
            owner="mvp",
        )
        arm = ArmVariant(
            experiment_id=experiment_id,
            arm_id="control",
            treatment_description="Fallback stub arm",
            structured_parameters_json={"ux_flow": "v1"},
            treatment_type="baseline",
            constraints_tag="default",
        )
        memory = ExperimentMemory(
            experiment_id=experiment_id,
            summary_text="Fallback retrieval stub (benchmark bundle missing for this id).",
        )
        metrics = [
            MetricsSummary(
                experiment_id=experiment_id,
                arm_id="control",
                sample_size=1200,
                conversion=0.13,
                retention=0.4,
                variance=0.02,
                confidence_interval=[0.11, 0.15],
            )
        ]
        return {
            "experiment": experiment,
            "arms": [arm],
            "memory": memory,
            "metrics": metrics,
            "benchmark_dir": str(benchmark_dir),
            "source": "fallback_stub",
        }
