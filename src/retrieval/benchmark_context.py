"""Load orchestration context from synthetic benchmark parquets."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Optional

import pandas as pd

from src.data.models import ArmVariant, Experiment, ExperimentMemory, MetricsSummary
from src.validation.benchmark_loader import BENCHMARK_TABLES, load_benchmark_tables

DEFAULT_BENCHMARK_DIR = Path("synthetic_env/benchmarks/generated_sanity_calibrated")


def resolve_benchmark_dir(explicit: Optional[str | Path] = None) -> Path:
    if explicit is not None:
        return Path(explicit)
    return Path(os.getenv("BENCHMARK_DATA_DIR", str(DEFAULT_BENCHMARK_DIR)))


def _parse_traffic_split(raw: Any) -> dict[str, float]:
    if isinstance(raw, dict):
        return {str(k): float(v) for k, v in raw.items()}
    if isinstance(raw, str) and raw.strip():
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return {str(k): float(v) for k, v in parsed.items()}
    return {}


def _parse_json_field(raw: Any) -> dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str) and raw.strip():
        parsed = json.loads(raw)
        if isinstance(parsed, dict):
            return parsed
    return {}


def _string_list_field(raw: Any) -> list[str]:
    if isinstance(raw, list):
        return [str(item) for item in raw]
    if isinstance(raw, str) and raw.strip():
        if "," in raw:
            return [part.strip() for part in raw.split(",") if part.strip()]
        return [raw.strip()]
    return []


def _row_to_experiment(row: pd.Series, objective_override: Optional[str] = None) -> Experiment:
    return Experiment(
        experiment_id=str(row["experiment_id"]),
        objective=objective_override or str(row.get("objective", "day7_retention")),
        start_date=row.get("start_date"),
        end_date=row.get("end_date"),
        status=str(row.get("status", "active")),
        traffic_split=_parse_traffic_split(row.get("traffic_split")),
        owner=row.get("owner"),
        notes=row.get("notes"),
    )


def _resolve_experiment_id(
    tables: dict[str, pd.DataFrame],
    experiment_id: str,
) -> Optional[str]:
    experiments = tables["experiments"]
    if experiment_id in experiments["experiment_id"].astype(str).values:
        return experiment_id
    if not experiments.empty:
        return str(experiments.iloc[0]["experiment_id"])
    return None


def load_context_from_benchmark(
    benchmark_dir: Path,
    experiment_id: str,
    objective: str,
) -> Optional[dict[str, Any]]:
    """Build retrieval context when benchmark parquets exist for the experiment."""
    tables = load_benchmark_tables(benchmark_dir, experiment_id=None)
    if tables is None:
        return None

    resolved_id = _resolve_experiment_id(tables, experiment_id)
    if resolved_id is None:
        return None

    filtered = load_benchmark_tables(benchmark_dir, experiment_id=resolved_id)
    if filtered is None:
        return None

    exp_rows = filtered["experiments"]
    if exp_rows.empty:
        return None

    experiment = _row_to_experiment(exp_rows.iloc[0], objective_override=objective)

    arms = [
        ArmVariant(
            experiment_id=str(row["experiment_id"]),
            arm_id=str(row["arm_id"]),
            treatment_description=str(row.get("treatment_description", row["arm_id"])),
            structured_parameters_json=_parse_json_field(row.get("structured_parameters_json")),
            treatment_type=str(row.get("treatment_type", "configured_bundle")),
            constraints_tag=row.get("constraints_tag"),
        )
        for _, row in filtered["arms"].iterrows()
    ]

    metrics = [
        MetricsSummary(
            experiment_id=str(row["experiment_id"]),
            arm_id=str(row["arm_id"]),
            sample_size=int(row["sample_size"]),
            conversion=float(row["conversion"]) if pd.notna(row.get("conversion")) else None,
            retention=float(row["retention"]) if pd.notna(row.get("retention")) else None,
            engagement=float(row["engagement"]) if pd.notna(row.get("engagement")) else None,
            revenue_proxy=float(row["revenue_proxy"]) if pd.notna(row.get("revenue_proxy")) else None,
            variance=float(row["variance"]) if pd.notna(row.get("variance")) else None,
            confidence_interval=_confidence_interval(row.get("confidence_interval")),
        )
        for _, row in filtered["metrics_summary"].iterrows()
    ]

    memory_path = benchmark_dir / "experiment_memory.parquet"
    memory: ExperimentMemory
    if memory_path.exists():
        mem_df = pd.read_parquet(memory_path)
        mem_df = mem_df[mem_df["experiment_id"].astype(str) == resolved_id]
        if not mem_df.empty:
            mem_row = mem_df.iloc[0]
            memory = ExperimentMemory(
                experiment_id=resolved_id,
                summary_text=str(mem_row.get("summary_text", "")),
                lessons_learned=_string_list_field(mem_row.get("lessons_learned")),
                winning_patterns=_string_list_field(mem_row.get("winning_patterns")),
                failed_patterns=_string_list_field(mem_row.get("failed_patterns")),
                analyst_notes=mem_row.get("analyst_notes"),
            )
        else:
            memory = _default_memory(resolved_id)
    else:
        memory = _default_memory(resolved_id)

    return {
        "experiment": experiment,
        "arms": arms,
        "metrics": metrics,
        "memory": memory,
        "benchmark_dir": str(benchmark_dir),
        "data_source": "benchmark",
        "resolved_experiment_id": resolved_id,
        "benchmark_tables_loaded": list(BENCHMARK_TABLES),
    }


def _confidence_interval(raw: Any) -> list[float]:
    if raw is None or (isinstance(raw, float) and pd.isna(raw)):
        return []
    if hasattr(raw, "tolist"):
        return [float(x) for x in raw.tolist()]
    if isinstance(raw, (list, tuple)):
        return [float(x) for x in raw]
    if isinstance(raw, str) and raw.strip():
        parsed = json.loads(raw)
        if isinstance(parsed, list):
            return [float(x) for x in parsed]
    return []


def _default_memory(experiment_id: str) -> ExperimentMemory:
    return ExperimentMemory(
        experiment_id=experiment_id,
        summary_text="No experiment_memory.parquet row found; using placeholder memory.",
        lessons_learned=[],
        winning_patterns=[],
        failed_patterns=[],
        analyst_notes="Retrieved from benchmark metrics only.",
    )
