"""Load retrieval context from frozen benchmark parquets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from src.data.models import ArmVariant, Experiment, ExperimentMemory, MetricsSummary
from src.validation.benchmark_loader import load_benchmark_tables


def _parse_json_field(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return default
    return default


def _split_memory_field(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    text = str(value).strip()
    return [text] if text else []


def load_benchmark_context(
    benchmark_dir: Path,
    experiment_id: str,
    *,
    objective: str | None = None,
) -> dict[str, Any] | None:
    tables = load_benchmark_tables(benchmark_dir, experiment_id=experiment_id)
    if tables is None:
        return None

    exp_row = tables["experiments"].iloc[0].to_dict()
    experiment = Experiment(
        experiment_id=str(exp_row["experiment_id"]),
        objective=objective or str(exp_row.get("objective") or ""),
        start_date=exp_row.get("start_date"),
        end_date=exp_row.get("end_date"),
        status=str(exp_row.get("status") or "active"),
        traffic_split=_parse_json_field(exp_row.get("traffic_split"), {}),
        owner="benchmark",
        notes=str(exp_row.get("notes") or "") or None,
    )

    arms: list[ArmVariant] = []
    for _, row in tables["arms"].iterrows():
        arms.append(
            ArmVariant(
                experiment_id=experiment_id,
                arm_id=str(row["arm_id"]),
                treatment_description=str(row.get("treatment_description") or ""),
                structured_parameters_json=_parse_json_field(row.get("structured_parameters_json"), {}),
                treatment_type=str(row.get("treatment_type") or "configured_bundle"),
                constraints_tag=str(row.get("constraints_tag") or "") or None,
            )
        )

    metrics: list[MetricsSummary] = []
    for _, row in tables["metrics_summary"].iterrows():
        ci = _parse_json_field(row.get("confidence_interval"), [])
        if not isinstance(ci, list):
            ci = []
        metrics.append(
            MetricsSummary(
                experiment_id=experiment_id,
                arm_id=str(row["arm_id"]),
                sample_size=int(row.get("sample_size") or 0),
                conversion=float(row["conversion"]) if row.get("conversion") is not None else None,
                retention=float(row["retention"]) if row.get("retention") is not None else None,
                engagement=float(row["engagement"]) if row.get("engagement") is not None else None,
                revenue_proxy=float(row["revenue_proxy"]) if row.get("revenue_proxy") is not None else None,
                variance=float(row["variance"]) if row.get("variance") is not None else None,
                confidence_interval=[float(x) for x in ci],
            )
        )

    memory_row = None
    memory_path = benchmark_dir / "experiment_memory.parquet"
    if memory_path.exists():
        import pandas as pd

        memory_df = pd.read_parquet(memory_path)
        memory_df = memory_df[memory_df["experiment_id"] == experiment_id]
        if not memory_df.empty:
            memory_row = memory_df.iloc[0].to_dict()

    if memory_row:
        memory = ExperimentMemory(
            experiment_id=experiment_id,
            summary_text=str(memory_row.get("summary_text") or ""),
            lessons_learned=_split_memory_field(memory_row.get("lessons_learned")),
            winning_patterns=_split_memory_field(memory_row.get("winning_patterns")),
            failed_patterns=_split_memory_field(memory_row.get("failed_patterns")),
            analyst_notes=str(memory_row.get("analyst_notes") or "") or None,
        )
    else:
        memory = ExperimentMemory(
            experiment_id=experiment_id,
            summary_text="No experiment memory in benchmark bundle.",
        )

    return {
        "experiment": experiment,
        "arms": arms,
        "memory": memory,
        "metrics": metrics,
        "benchmark_dir": str(benchmark_dir),
        "source": "benchmark_parquet",
    }
