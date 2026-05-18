"""Benchmark parquet validation using synthetic_env check primitives.

Loads tables via benchmark_loader and maps synthetic_env report sections to
ValidationCheck records (severity=warning). See docs/validation_agent.md.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from synthetic_env.validation.checks import create_validation_report

from src.validation.benchmark_loader import load_benchmark_tables
from src.validation.checks import _check

_BENCHMARK_SECTIONS = (
    ("structural_fidelity", "Benchmark structural fidelity check failed."),
    ("statistical_fidelity", "Benchmark statistical fidelity check failed."),
    ("behavioral_realism", "Benchmark behavioral realism check failed."),
    ("decision_usefulness", "Benchmark decision usefulness check failed."),
)


def run_benchmark_parquet_checks(
    benchmark_dir: Path,
    experiment_id: str,
) -> tuple[list[dict[str, Any]], bool]:
    tables = load_benchmark_tables(benchmark_dir, experiment_id=experiment_id)
    if tables is None:
        return [
            _check(
                "benchmark_data_available",
                True,
                "No benchmark parquet bundle found for this experiment; skipped benchmark checks.",
                severity="info",
                details={"benchmark_dir": str(benchmark_dir), "experiment_id": experiment_id},
            )
        ], False

    report = create_validation_report(
        population=tables["population"],
        experiments=tables["experiments"],
        arms=tables["arms"],
        observations=tables["observations"],
        metrics_summary=tables["metrics_summary"],
    )

    checks: list[dict[str, Any]] = [
        _check(
            "benchmark_data_available",
            True,
            "Benchmark parquet bundle loaded.",
            severity="info",
            details={"benchmark_dir": str(benchmark_dir), "experiment_id": experiment_id},
        ),
        _check(
            "benchmark_overall_pass",
            bool(report["overall_pass"]),
            "Benchmark overall quality gate failed.",
            severity="warning",
            details={"overall_pass": report["overall_pass"]},
        ),
    ]

    for section, failure_message in _BENCHMARK_SECTIONS:
        payload = report[section]
        checks.append(
            _check(
                f"benchmark_{section}",
                bool(payload["pass"]),
                failure_message,
                severity="warning",
                details=payload,
            )
        )

    return checks, True
