"""End-to-end synthetic benchmark generation pipeline."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from synthetic_env.outcome_simulator.simulator import (
    create_experiment_memory,
    simulate_observations,
    summarize_metrics,
)
from synthetic_env.synthetic_population.generator import generate_population
from synthetic_env.treatment_space.generator import generate_experiment_tables
from synthetic_env.validation.checks import create_validation_report, report_to_frame
from synthetic_env.world_spec.loader import load_world_spec


def run_generation(
    n_users: int = 5000,
    experiment_id: str = "exp_0001",
    seed: int = 42,
    output_dir: str | Path = "synthetic_env/benchmarks/generated",
) -> dict[str, pd.DataFrame]:
    spec = load_world_spec("configs/world_spec.yaml")
    population = generate_population(spec, n_users=n_users, seed=seed)
    experiments, arms = generate_experiment_tables(spec, experiment_id=experiment_id)
    observations = simulate_observations(population, experiment_id=experiment_id, arm_ids=arms["arm_id"].tolist(), seed=seed)
    metrics_summary = summarize_metrics(observations, experiment_id=experiment_id)
    experiment_memory = create_experiment_memory(metrics_summary, experiment_id=experiment_id)

    validation_report = create_validation_report(
        population=population,
        experiments=experiments,
        arms=arms,
        observations=observations,
        metrics_summary=metrics_summary,
    )
    validation_table = report_to_frame(validation_report)

    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)

    population.to_parquet(out / "population.parquet", index=False)
    experiments.to_parquet(out / "experiments.parquet", index=False)
    arms.to_parquet(out / "arms.parquet", index=False)
    observations.to_parquet(out / "observations.parquet", index=False)
    metrics_summary.to_parquet(out / "metrics_summary.parquet", index=False)
    experiment_memory.to_parquet(out / "experiment_memory.parquet", index=False)
    validation_table.to_parquet(out / "validation_report.parquet", index=False)

    return {
        "population": population,
        "experiments": experiments,
        "arms": arms,
        "observations": observations,
        "metrics_summary": metrics_summary,
        "experiment_memory": experiment_memory,
        "validation_report": validation_table,
    }
