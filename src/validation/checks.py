"""Rule-based validation checks on retrieval context (experiment, arms, metrics).

Used by the structural and metrics LangGraph nodes. See docs/validation_agent.md.
"""

from __future__ import annotations

from typing import Any, Literal

from src.data.models import ArmVariant, Experiment, MetricsSummary

Severity = Literal["error", "warning", "info"]
MIN_SAMPLE_SIZE = 100
MIN_RETENTION_SPREAD = 0.01
TRAFFIC_SUM_TOLERANCE = 0.01


def messages_from_checks(checks: list[dict[str, Any]], severity: Severity) -> list[str]:
    return [check["message"] for check in checks if not check["passed"] and check["severity"] == severity]


def _check(
    name: str,
    passed: bool,
    message: str,
    severity: Severity = "error",
    details: dict[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "name": name,
        "passed": passed,
        "message": message,
        "severity": severity,
        "details": details or {},
    }


def run_structural_checks(context: dict) -> list[dict[str, Any]]:
    experiment: Experiment = context["experiment"]
    arms: list[ArmVariant] = context.get("arms") or []
    checks: list[dict[str, Any]] = []

    if not experiment.traffic_split:
        checks.append(_check("traffic_split_present", False, "Missing traffic split."))
    else:
        traffic_sum = sum(experiment.traffic_split.values())
        checks.append(
            _check(
                "traffic_split_present",
                True,
                "Traffic split is configured.",
                severity="info",
                details={"arms": list(experiment.traffic_split.keys())},
            )
        )
        checks.append(
            _check(
                "traffic_split_sum",
                abs(traffic_sum - 1.0) <= TRAFFIC_SUM_TOLERANCE,
                "Traffic split should sum to 1.0.",
                severity="warning",
                details={"sum": round(traffic_sum, 4)},
            )
        )

    if not arms:
        checks.append(
            _check(
                "arms_present",
                False,
                "No treatment arms available for validation.",
                severity="warning",
            )
        )
    else:
        arm_ids = [arm.arm_id for arm in arms]
        checks.append(
            _check(
                "arms_present",
                True,
                f"Found {len(arms)} treatment arm(s).",
                severity="info",
                details={"arm_ids": arm_ids},
            )
        )
        checks.append(
            _check(
                "arm_ids_unique",
                len(arm_ids) == len(set(arm_ids)),
                "Duplicate arm_id values detected.",
            )
        )

    return checks


def run_metrics_checks(context: dict) -> list[dict[str, Any]]:
    experiment: Experiment = context["experiment"]
    metrics: list[MetricsSummary] = context.get("metrics") or []
    checks: list[dict[str, Any]] = []

    if not metrics:
        checks.append(_check("metrics_present", False, "No metrics summary available."))
        return checks

    checks.append(
        _check(
            "metrics_present",
            True,
            f"Found metrics for {len(metrics)} arm(s).",
            severity="info",
        )
    )

    if len(metrics) < 2:
        checks.append(
            _check(
                "multi_arm_metrics",
                False,
                "Only one treatment arm in metrics; causal comparison is limited.",
                severity="warning",
            )
        )

    traffic_arms = set(experiment.traffic_split.keys()) if experiment.traffic_split else set()
    metric_arms = {metric.arm_id for metric in metrics}
    if traffic_arms:
        checks.append(
            _check(
                "metrics_align_with_traffic",
                metric_arms.issubset(traffic_arms),
                "Metrics include arm_id values not present in traffic split.",
                severity="warning",
                details={"unexpected_arms": sorted(metric_arms - traffic_arms)},
            )
        )

    undersized = [metric.arm_id for metric in metrics if metric.sample_size < MIN_SAMPLE_SIZE]
    checks.append(
        _check(
            "sample_size_floor",
            not undersized,
            "One or more arms are below the minimum sample size floor.",
            severity="warning",
            details={"min_sample_size": MIN_SAMPLE_SIZE, "undersized_arms": undersized},
        )
    )

    retentions = [metric.retention for metric in metrics if metric.retention is not None]
    if retentions:
        spread = max(retentions) - min(retentions)
        checks.append(
            _check(
                "decision_usefulness",
                spread >= MIN_RETENTION_SPREAD,
                "Retention spread across arms is very small; benchmark may be too trivial.",
                severity="warning",
                details={"retention_spread": round(spread, 4)},
            )
        )

    return checks
