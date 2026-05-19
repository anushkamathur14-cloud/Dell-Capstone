"""BenchmarkRepository — single adapter for the frozen benchmark parquets.

Slice A architectural choice (per Issue #1 option 1): isolate all parquet
I/O behind one class so:

    - the retrieval skill stays a thin caller,
    - swapping the backend later (Postgres, S3, in-memory) is one edit,
    - tests can pass any path-like directory and exercise the same code,
    - column-name constants live in exactly one file.

The class is intentionally minimal: one method per parquet, returning
already-parsed Python primitives. No filtering logic beyond `experiment_id`
matching; downstream skills own their own slicing.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

import pyarrow.parquet as pq

logger = logging.getLogger(__name__)

# Filenames in the frozen benchmark directory. Update here only.
EXPERIMENTS_FILE = "experiments.parquet"
ARMS_FILE = "arms.parquet"
METRICS_FILE = "metrics_summary.parquet"
OBSERVATIONS_FILE = "observations.parquet"
POPULATION_FILE = "population.parquet"
MEMORY_FILE = "experiment_memory.parquet"

# Identifier columns shared across parquets.
COL_EXPERIMENT_ID = "experiment_id"
COL_ARM_ID = "arm_id"

# arms.parquet has no is_control column; arm_id == CONTROL_ARM_ID is the
# convention used by the synthetic_env generator.
CONTROL_ARM_ID = "control"


class BenchmarkRepositoryError(RuntimeError):
    """Raised when a benchmark file is missing or a query cannot be satisfied."""


class BenchmarkRepository:
    """Read-only adapter over the calibrated benchmark parquets.

    Parameters
    ----------
    benchmark_dir
        Path to the directory holding the parquet files. Defaults to the
        frozen `benchmark_v1_delayed_effects_pass` location under
        `synthetic_env/`. Tests pass a fixture directory here.
    """

    def __init__(self, benchmark_dir: Path | str) -> None:
        self.benchmark_dir = Path(benchmark_dir)
        if not self.benchmark_dir.exists():
            raise BenchmarkRepositoryError(
                f"Benchmark directory not found: {self.benchmark_dir}"
            )

    # ------------------------------------------------------------------ #
    # Internal helpers                                                   #
    # ------------------------------------------------------------------ #

    def _read(self, filename: str) -> list[dict[str, Any]]:
        path = self.benchmark_dir / filename
        if not path.exists():
            raise BenchmarkRepositoryError(f"Benchmark file missing: {path}")
        return pq.read_table(path).to_pylist()

    @staticmethod
    def _filter_by_experiment(
        rows: list[dict[str, Any]], experiment_id: str
    ) -> list[dict[str, Any]]:
        return [r for r in rows if r.get(COL_EXPERIMENT_ID) == experiment_id]

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #

    def get_experiment(self, experiment_id: str) -> dict[str, Any]:
        """Return the single row for `experiment_id` from experiments.parquet."""
        rows = self._read(EXPERIMENTS_FILE)
        matching = self._filter_by_experiment(rows, experiment_id)
        if not matching:
            available = [r.get(COL_EXPERIMENT_ID) for r in rows]
            raise BenchmarkRepositoryError(
                f"experiment_id={experiment_id!r} not found in "
                f"{EXPERIMENTS_FILE}. Available: {available}"
            )
        if len(matching) > 1:
            logger.warning(
                "Multiple rows for experiment_id=%s in %s; using first.",
                experiment_id,
                EXPERIMENTS_FILE,
            )
        return matching[0]

    def get_arms(self, experiment_id: str) -> list[dict[str, Any]]:
        """Return arm rows for `experiment_id`, parsing the JSON params.

        `structured_parameters_json` is parsed in place into a dict so the
        downstream ArmVariant model can accept the field as `dict[str, Any]`.
        """
        rows = self._filter_by_experiment(
            self._read(ARMS_FILE), experiment_id
        )
        if not rows:
            raise BenchmarkRepositoryError(
                f"No arms found for experiment_id={experiment_id!r} "
                f"in {ARMS_FILE}"
            )
        for row in rows:
            params_raw = row.get("structured_parameters_json")
            if isinstance(params_raw, str):
                try:
                    row["structured_parameters_json"] = json.loads(params_raw)
                except json.JSONDecodeError as exc:
                    logger.warning(
                        "Failed to parse structured_parameters_json for "
                        "arm_id=%s: %s",
                        row.get(COL_ARM_ID),
                        exc,
                    )
                    row["structured_parameters_json"] = {}
            elif params_raw is None:
                row["structured_parameters_json"] = {}
        return rows

    def get_metrics(self, experiment_id: str) -> list[dict[str, Any]]:
        """Return per-arm KPI rows for `experiment_id`."""
        rows = self._filter_by_experiment(
            self._read(METRICS_FILE), experiment_id
        )
        if not rows:
            raise BenchmarkRepositoryError(
                f"No metrics rows for experiment_id={experiment_id!r} "
                f"in {METRICS_FILE}"
            )
        return rows

    def get_observations(self, experiment_id: str) -> list[dict[str, Any]]:
        """Return user-level event rows for `experiment_id`.

        Parses context_features_json and outcomes_json in place so the
        Observation model can accept them as dicts (matches the existing
        contract in src/data/models.py).
        """
        rows = self._filter_by_experiment(
            self._read(OBSERVATIONS_FILE), experiment_id
        )
        for row in rows:
            for json_col in ("context_features_json", "outcomes_json"):
                raw = row.get(json_col)
                if isinstance(raw, str):
                    try:
                        row[json_col] = json.loads(raw)
                    except json.JSONDecodeError:
                        row[json_col] = {}
                elif raw is None:
                    row[json_col] = {}
        return rows

    def get_memory(self, experiment_id: str) -> dict[str, Any] | None:
        """Return the narrative-memory row for `experiment_id` if present."""
        rows = self._filter_by_experiment(
            self._read(MEMORY_FILE), experiment_id
        )
        if not rows:
            return None
        if len(rows) > 1:
            logger.warning(
                "Multiple memory rows for experiment_id=%s; using first.",
                experiment_id,
            )
        return rows[0]
