"""World-spec constraint checks (warnings only — do not halt the pipeline)."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from src.data.models import ArmVariant, Experiment, MetricsSummary
from src.validation.benchmark_loader import load_benchmark_tables
from src.validation.checks import _check

DEFAULT_WORLD_SPEC_PATH = Path("configs/world_spec.yaml")


def _load_world_spec(path: Path = DEFAULT_WORLD_SPEC_PATH) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def run_world_spec_checks(
    context: dict,
    benchmark_dir: Path | None = None,
    world_spec_path: Path = DEFAULT_WORLD_SPEC_PATH,
) -> list[dict[str, Any]]:
    spec = _load_world_spec(world_spec_path)
    if not spec:
        return [
            _check(
                "world_spec_loaded",
                True,
                "World spec not found; skipped constraint warnings.",
                severity="info",
            )
        ]

    checks: list[dict[str, Any]] = [
        _check(
            "world_spec_loaded",
            True,
            "World spec constraints evaluated as warnings.",
            severity="info",
            details={"path": str(world_spec_path)},
        )
    ]

    experiment: Experiment = context["experiment"]
    arms: list[ArmVariant] = context.get("arms") or []
    metrics: list[MetricsSummary] = context.get("metrics") or []

    risk_limits = (spec.get("constraints") or {}).get("risk_limits") or {}
    min_satisfaction = risk_limits.get("min_expected_satisfaction_proxy")
    if min_satisfaction is not None and benchmark_dir:
        tables = load_benchmark_tables(benchmark_dir, experiment_id=experiment.experiment_id)
        if tables is not None and "satisfaction_proxy" in tables["observations"].columns:
            mean_satisfaction = float(tables["observations"]["satisfaction_proxy"].mean())
            checks.append(
                _check(
                    "world_spec_min_satisfaction_proxy",
                    mean_satisfaction >= float(min_satisfaction),
                    "Mean satisfaction proxy is below world-spec risk limit.",
                    severity="warning",
                    details={
                        "mean_satisfaction_proxy": round(mean_satisfaction, 4),
                        "min_expected_satisfaction_proxy": min_satisfaction,
                    },
                )
            )

    traffic_rules = (spec.get("constraints") or {}).get("traffic_rules") or {}
    max_aggressive = traffic_rules.get("max_aggressive_traffic_share")
    if max_aggressive is not None and experiment.traffic_split and arms:
        aggressive_share = sum(
            experiment.traffic_split.get(arm.arm_id, 0.0)
            for arm in arms
            if arm.constraints_tag in {"growth", "aggressive"}
            or "aggressive" in (arm.treatment_description or "").lower()
        )
        checks.append(
            _check(
                "world_spec_max_aggressive_traffic",
                aggressive_share <= float(max_aggressive),
                "Aggressive-tagged traffic share exceeds world-spec cap.",
                severity="warning",
                details={
                    "aggressive_traffic_share": round(aggressive_share, 4),
                    "max_aggressive_traffic_share": max_aggressive,
                },
            )
        )

    if metrics and min_satisfaction is not None:
        low_retention_arms = [
            metric.arm_id
            for metric in metrics
            if metric.retention is not None and metric.retention < float(min_satisfaction)
        ]
        if low_retention_arms:
            checks.append(
                _check(
                    "world_spec_retention_floor_proxy",
                    False,
                    "One or more arms have retention below the world-spec satisfaction proxy floor (warning proxy).",
                    severity="warning",
                    details={"arms": low_retention_arms, "floor": min_satisfaction},
                )
            )

    return checks
