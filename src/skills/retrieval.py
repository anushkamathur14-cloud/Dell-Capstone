from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from langsmith import traceable

from src.data.benchmark_repository import (
    BenchmarkRepository,
    BenchmarkRepositoryError,
    CONTROL_ARM_ID,
)
from src.data.models import (
    ArmVariant,
    Experiment,
    ExperimentMemory,
    MetricsSummary,
)
from src.observability.langsmith_trace import TraceNames

logger = logging.getLogger(__name__)

# Default benchmark directory relative to repo root. Override via the
# constructor when running tests or notebooks.
DEFAULT_BENCHMARK_DIR = Path(
    "synthetic_env/benchmarks/generated_sanity_calibrated"
)

# Schema version for the bundle shape produced by this skill. Bump on any
# breaking change to the returned dict per implementation_plan_v1.md §7.
SCHEMA_VERSION = "1.0.0"

# experiments.parquet does not carry an `owner` column, but the Experiment
# model requires `owner: str | None`. The stub used "mvp"; preserved here.
DEFAULT_EXPERIMENT_OWNER = "mvp"


class RetrievalError(RuntimeError):
    """Raised when retrieval cannot satisfy the request.

    Wraps `BenchmarkRepositoryError` so the orchestrator only needs to
    know about retrieval-level exceptions.
    """


def _coerce_lessons_learned(raw: Any) -> list[str]:
    """experiment_memory.parquet stores lessons_learned as a single string;
    src/data/models.py declares it as list[str]. Coerce defensively so
    neither side has to change.
    """
    if raw is None or raw == "":
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw]
    if isinstance(raw, str):
        # Split on '. ' to recover sentence-level lessons; trim empties.
        parts = [p.strip() for p in raw.split(".") if p.strip()]
        return parts or [raw]
    return [str(raw)]


def _coerce_pattern_list(raw: Any) -> list[str]:
    """winning_patterns / failed_patterns are list[str] in the model but
    arrive as a single string from the parquet (e.g. 'fast_progression').
    """
    if raw is None or raw == "":
        return []
    if isinstance(raw, list):
        return [str(x) for x in raw]
    return [str(raw)]


class RetrievalSkill:
    """Loads benchmark context for one experiment.

    The orchestrator constructs the skill once and calls `run` per request:

        skill = RetrievalSkill()
        bundle = skill.run(objective="day7_retention",
                           experiment_id="exp_sanity_001_calibrated")

    Tests inject a fixture directory:

        skill = RetrievalSkill(benchmark_dir="tests/fixtures/benchmark_slice_a")
    """

    def __init__(
        self, benchmark_dir: Path | str | None = None
    ) -> None:
        self.benchmark_dir = (
            Path(benchmark_dir) if benchmark_dir else DEFAULT_BENCHMARK_DIR
        )

    # ------------------------------------------------------------------ #
    # Public API                                                         #
    # ------------------------------------------------------------------ #

    @traceable(name=TraceNames.RETRIEVAL_SKILL)
    def run(self, objective: str, experiment_id: str) -> dict[str, Any]:
        """Retrieve the benchmark context bundle for one experiment.

        Returns
        -------
        dict
            ``{experiment, arms, memory, metrics}`` matching the existing
            stub's contract. Models are the team-defined Pydantic classes
            from `src/data/models.py`. Plus ``schema_version`` so future
            consumers can branch on shape changes.

        Raises
        ------
        RetrievalError
            If the benchmark files are missing, the experiment_id is
            unknown, or no arms / metrics rows exist for it.
        """
        logger.info(
            "retrieval_skill: experiment_id=%s objective=%s benchmark_dir=%s",
            experiment_id,
            objective,
            self.benchmark_dir,
        )

        try:
            repo = BenchmarkRepository(self.benchmark_dir)
            experiment_row = repo.get_experiment(experiment_id)
            arm_rows = repo.get_arms(experiment_id)
            metric_rows = repo.get_metrics(experiment_id)
            memory_row = repo.get_memory(experiment_id)
        except BenchmarkRepositoryError as exc:
            raise RetrievalError(str(exc)) from exc

        experiment = self._build_experiment(experiment_row, objective)
        arms = self._build_arms(arm_rows)
        memory = self._build_memory(memory_row, experiment_id)
        metrics = self._build_metrics(metric_rows)

        return {
            "schema_version": SCHEMA_VERSION,
            "experiment": experiment,
            "arms": arms,
            "memory": memory,
            "metrics": metrics,
        }

    # ------------------------------------------------------------------ #
    # Builders                                                           #
    # ------------------------------------------------------------------ #

    def _build_experiment(
        self, row: dict[str, Any], objective_arg: str
    ) -> Experiment:
        """Build the Experiment model, validating the caller's objective."""
        parquet_objective = row.get("objective")
        if parquet_objective and parquet_objective != objective_arg:
            logger.warning(
                "Caller objective=%r does not match benchmark objective=%r "
                "for experiment_id=%s; using benchmark value.",
                objective_arg,
                parquet_objective,
                row.get("experiment_id"),
            )

        traffic_split = row.get("traffic_split")
        if isinstance(traffic_split, str):
            import json

            try:
                traffic_split = json.loads(traffic_split)
            except json.JSONDecodeError:
                logger.warning(
                    "Could not parse traffic_split=%r; using empty dict.",
                    traffic_split,
                )
                traffic_split = {}
        elif traffic_split is None:
            traffic_split = {}

        return Experiment(
            experiment_id=row["experiment_id"],
            objective=parquet_objective or objective_arg,
            start_date=row.get("start_date"),
            end_date=row.get("end_date"),
            status=row.get("status", "unknown"),
            traffic_split={k: float(v) for k, v in traffic_split.items()},
            owner=row.get("owner", DEFAULT_EXPERIMENT_OWNER),
            notes=row.get("notes"),
        )

    def _build_arms(self, rows: list[dict[str, Any]]) -> list[ArmVariant]:
        """Build ArmVariant models from arm rows."""
        return [
            ArmVariant(
                experiment_id=row["experiment_id"],
                arm_id=row["arm_id"],
                treatment_description=row.get("treatment_description", ""),
                structured_parameters_json=row.get(
                    "structured_parameters_json", {}
                ),
                treatment_type=row.get("treatment_type", "unknown"),
                constraints_tag=row.get("constraints_tag"),
            )
            for row in rows
        ]

    def _build_memory(
        self,
        memory_row: dict[str, Any] | None,
        experiment_id: str,
    ) -> ExperimentMemory:
        """Build the ExperimentMemory model.

        Returns an empty bundle (all fields blank/empty) if no row exists
        for the experiment; missing memory is not an error.
        """
        if memory_row is None:
            return ExperimentMemory(
                experiment_id=experiment_id,
                summary_text="",
                lessons_learned=[],
                winning_patterns=[],
                failed_patterns=[],
                analyst_notes=(
                    f"No memory row found for "
                    f"experiment_id={experiment_id!r}."
                ),
            )
        return ExperimentMemory(
            experiment_id=memory_row["experiment_id"],
            summary_text=memory_row.get("summary_text", ""),
            lessons_learned=_coerce_lessons_learned(
                memory_row.get("lessons_learned")
            ),
            winning_patterns=_coerce_pattern_list(
                memory_row.get("winning_patterns")
            ),
            failed_patterns=_coerce_pattern_list(
                memory_row.get("failed_patterns")
            ),
            analyst_notes=memory_row.get("analyst_notes"),
        )

    def _build_metrics(
        self, rows: list[dict[str, Any]]
    ) -> list[MetricsSummary]:
        """Build per-arm MetricsSummary models."""
        return [
            MetricsSummary(
                experiment_id=row["experiment_id"],
                arm_id=row["arm_id"],
                sample_size=int(row["sample_size"]),
                conversion=row.get("conversion"),
                retention=row.get("retention"),
                engagement=row.get("engagement"),
                revenue_proxy=row.get("revenue_proxy"),
                variance=row.get("variance"),
                confidence_interval=list(row.get("confidence_interval") or []),
            )
            for row in rows
        ]

    # ------------------------------------------------------------------ #
    # Helpers                                                            #
    # ------------------------------------------------------------------ #

    @staticmethod
    def is_control(arm: ArmVariant) -> bool:
        """Convention: an arm is the control iff arm_id == 'control'.

        Exposed as a static helper so downstream skills don't reinvent
        the convention. If the team adds an explicit control flag to
        ArmVariant later, this is the one line to change.
        """
        return arm.arm_id == CONTROL_ARM_ID
