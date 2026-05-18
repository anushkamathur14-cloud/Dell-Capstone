"""Load benchmark parquet tables for validation."""

from __future__ import annotations

from pathlib import Path

import pandas as pd

BENCHMARK_TABLES = (
    "population",
    "experiments",
    "arms",
    "observations",
    "metrics_summary",
)


def load_benchmark_tables(benchmark_dir: Path, experiment_id: str | None = None) -> dict[str, pd.DataFrame] | None:
    """Load benchmark tables if all required parquet files exist."""
    if not benchmark_dir.is_dir():
        return None

    tables: dict[str, pd.DataFrame] = {}
    for name in BENCHMARK_TABLES:
        path = benchmark_dir / f"{name}.parquet"
        if not path.exists():
            return None
        tables[name] = pd.read_parquet(path)

    if experiment_id:
        tables["experiments"] = tables["experiments"][tables["experiments"]["experiment_id"] == experiment_id]
        if tables["experiments"].empty:
            return None
        for name in ("arms", "observations", "metrics_summary"):
            tables[name] = tables[name][tables[name]["experiment_id"] == experiment_id]

    return tables
