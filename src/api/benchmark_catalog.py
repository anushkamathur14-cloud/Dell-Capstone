"""Read-only experiment / run catalog from benchmark parquets (for Lovable dashboards)."""

from __future__ import annotations

from datetime import date, datetime
from pathlib import Path
from typing import Any

import pandas as pd
from fastapi import APIRouter, HTTPException

from src.config.settings import get_settings
from src.validation.benchmark_loader import BENCHMARK_TABLES, load_benchmark_tables

router = APIRouter(tags=["catalog"])


def _benchmark_dir() -> Path:
    return Path(get_settings().benchmark_data_dir)


def _jsonable_row(row: dict[str, Any]) -> dict[str, Any]:
    out: dict[str, Any] = {}
    for k, v in row.items():
        if v is None or (isinstance(v, float) and pd.isna(v)):
            out[k] = None
        elif isinstance(v, (str, int, float, bool)):
            out[k] = v
        elif isinstance(v, (datetime, date)):
            out[k] = v.isoformat()
        elif hasattr(v, "item"):  # numpy scalar
            try:
                out[k] = v.item()
            except Exception:
                out[k] = str(v)
        else:
            out[k] = str(v)
    return out


@router.get("/experiments")
def list_experiments() -> dict[str, Any]:
    """All experiment rows from ``experiments.parquet`` (benchmark bundle)."""
    root = _benchmark_dir()
    path = root / "experiments.parquet"
    if not path.exists():
        return {
            "benchmark_data_dir": str(root),
            "experiments": [],
            "source": "none",
            "detail": "experiments.parquet not found; check BENCHMARK_DATA_DIR",
        }
    df = pd.read_parquet(path)
    experiments = [_jsonable_row(r) for r in df.to_dict(orient="records")]
    return {
        "benchmark_data_dir": str(root),
        "experiments": experiments,
        "source": "benchmark_parquet",
        "bundle_ready": all((root / f"{n}.parquet").exists() for n in BENCHMARK_TABLES),
    }


@router.get("/runs")
def list_runs() -> dict[str, Any]:
    """Benchmark registry rows plus **persisted** ``POST /orchestrate`` history (demo SQLite).

    - ``runs``: parquet-backed IDs you can orchestrate.
    - ``orchestrations``: recent server-side orchestrate calls (see ``run_record_id`` on POST body).
    """
    from src.api.orchestrate_history import list_orchestration_summaries

    root = _benchmark_dir()
    path = root / "experiments.parquet"
    reg_runs: list[dict[str, Any]] = []
    if path.exists():
        df = pd.read_parquet(path)
        for row in df.to_dict(orient="records"):
            jr = _jsonable_row(row)
            eid = str(jr.get("experiment_id", "") or "")
            reg_runs.append(
                {
                    "run_id": eid,
                    "experiment_id": eid,
                    "status": "registry",
                    "objective": jr.get("objective"),
                    "experiment_status": jr.get("status"),
                    "kind": "benchmark_registry",
                    "note": "Benchmark registry row; POST /orchestrate/{run_id} to execute the full pipeline.",
                }
            )
    bundle_ready = all((root / f"{n}.parquet").exists() for n in BENCHMARK_TABLES)
    orchestrations = list_orchestration_summaries(limit=100)
    return {
        "benchmark_data_dir": str(root),
        "runs": reg_runs,
        "orchestrations": orchestrations,
        "source": "benchmark_registry+demo_history",
        "bundle_ready": bundle_ready,
    }


@router.get("/runs/{run_id}")
def get_run(run_id: str) -> dict[str, Any]:
    """If ``run_id`` is a UUID, return a persisted orchestrate row; else benchmark parquet snapshot."""
    from src.api.orchestrate_history import get_orchestration_detail, is_persisted_run_id

    if is_persisted_run_id(run_id):
        detail = get_orchestration_detail(run_id)
        if detail is not None:
            return detail
        raise HTTPException(status_code=404, detail=f"No orchestration record: {run_id}")

    root = _benchmark_dir()
    tables = load_benchmark_tables(root, experiment_id=run_id)
    if tables is None:
        exp_path = root / "experiments.parquet"
        if exp_path.exists():
            df = pd.read_parquet(exp_path)
            if run_id not in set(df["experiment_id"].astype(str)):
                raise HTTPException(status_code=404, detail=f"Unknown experiment_id: {run_id}")
        raise HTTPException(
            status_code=404,
            detail=f"No benchmark bundle for {run_id} under {root} (missing parquets or experiment row).",
        )
    exp_row = _jsonable_row(tables["experiments"].iloc[0].to_dict())
    n_arms = len(tables["arms"])
    n_metrics = len(tables["metrics_summary"])
    n_obs = len(tables["observations"])
    memory_preview: str | None = None
    mem_path = root / "experiment_memory.parquet"
    if mem_path.exists():
        mem_df = pd.read_parquet(mem_path)
        sub = mem_df[mem_df["experiment_id"].astype(str) == run_id]
        if not sub.empty and "summary_text" in sub.columns:
            memory_preview = str(sub.iloc[0].get("summary_text") or "")[:500] or None
    return {
        "run_id": run_id,
        "experiment_id": run_id,
        "source": "benchmark_parquet",
        "benchmark_data_dir": str(root),
        "experiment": exp_row,
        "counts": {"arms": n_arms, "metrics_summary": n_metrics, "observations": n_obs},
        "memory_summary_preview": memory_preview,
        "note": "Registry snapshot from parquets; POST /orchestrate/{run_id} for full pipeline output.",
    }
