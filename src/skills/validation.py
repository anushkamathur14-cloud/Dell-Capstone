"""Validation skill: all check logic; ValidationAgent nodes call these steps (4A)."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal, Optional, Union

from src.data.models import ValidationReport
from src.validation.benchmark_checks import run_benchmark_parquet_checks
from src.validation.checks import messages_from_checks, run_metrics_checks, run_structural_checks
from src.validation.llm_diagnostics import generate_diagnostics_summary
from src.validation.world_spec_checks import run_world_spec_checks

Decision = Literal["go", "caution", "stop"]
DEFAULT_BENCHMARK_DIR = Path("synthetic_env/benchmarks/generated_sanity_calibrated")


def _partition_checks(checks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "checks": checks,
        "issues": messages_from_checks(checks, "error"),
        "warnings": messages_from_checks(checks, "warning"),
    }


class ValidationSkill:
    def __init__(self, benchmark_dir: Optional[Union[Path, str]] = None) -> None:
        self._benchmark_dir = Path(benchmark_dir) if benchmark_dir else None

    def run_structural(self, context: dict[str, Any]) -> dict[str, Any]:
        return _partition_checks(run_structural_checks(context))

    def run_metrics(self, context: dict[str, Any]) -> dict[str, Any]:
        return _partition_checks(run_metrics_checks(context))

    def run_benchmark(self, context: dict[str, Any], benchmark_dir: Optional[str] = None) -> dict[str, Any]:
        experiment_id = context["experiment"].experiment_id
        directory = Path(benchmark_dir or context.get("benchmark_dir") or self._benchmark_dir or DEFAULT_BENCHMARK_DIR)
        checks, loaded = run_benchmark_parquet_checks(directory, experiment_id)
        result = _partition_checks(checks)
        result["benchmark_loaded"] = loaded
        return result

    def run_world_spec(self, context: dict[str, Any], benchmark_dir: Optional[str] = None) -> dict[str, Any]:
        experiment_id = context["experiment"].experiment_id
        directory = Path(benchmark_dir or context.get("benchmark_dir") or self._benchmark_dir or DEFAULT_BENCHMARK_DIR)
        checks = run_world_spec_checks(context, benchmark_dir=directory)
        return _partition_checks(checks)

    def run_decide(self, issues: list[str], warnings: list[str]) -> dict[str, Any]:
        if len(issues) >= 2:
            decision: Decision = "stop"
        elif issues or warnings:
            decision = "caution"
        else:
            decision = "go"
        return {"decision": decision}

    def run_diagnostics(
        self,
        decision: str,
        issues: list[str],
        warnings: list[str],
        checks: list[dict[str, Any]],
        enable_llm: bool = False,
    ) -> dict[str, Any]:
        summary, source = generate_diagnostics_summary(
            decision=decision,
            issues=issues,
            warnings=warnings,
            checks=checks,
            use_llm=enable_llm,
        )
        return {"diagnostics_summary": summary, "diagnostics_source": source}

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        benchmark_dir = context.get("benchmark_dir") or self._benchmark_dir
        enable_llm = bool(context.get("enable_llm", False))

        checks: list[dict[str, Any]] = []
        issues: list[str] = []
        warnings: list[str] = []
        benchmark_loaded = False

        for step in (
            self.run_structural(context),
            self.run_metrics(context),
            self.run_benchmark(context, str(benchmark_dir) if benchmark_dir else None),
            self.run_world_spec(context, str(benchmark_dir) if benchmark_dir else None),
        ):
            checks.extend(step["checks"])
            issues.extend(step["issues"])
            warnings.extend(step["warnings"])
            benchmark_loaded = benchmark_loaded or step.get("benchmark_loaded", False)

        decision = self.run_decide(issues, warnings)["decision"]
        diagnostics = self.run_diagnostics(decision, issues, warnings, checks, enable_llm=enable_llm)

        report = ValidationReport(
            decision=decision,
            issues=issues,
            warnings=warnings,
            checks=checks,
            benchmark_loaded=benchmark_loaded,
            diagnostics_summary=diagnostics["diagnostics_summary"],
            diagnostics_source=diagnostics["diagnostics_source"],
        )
        return report.model_dump()
