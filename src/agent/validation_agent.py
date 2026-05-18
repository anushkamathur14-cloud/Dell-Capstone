"""LangGraph validation agent for experiment context quality gating.

Orchestrates structural, metrics, benchmark-parquet, and world-spec checks, then
emits a ValidationReport (go/caution/stop) plus optional LLM diagnostics.

See docs/validation_agent.md for architecture, decision policy, and usage.
"""

from __future__ import annotations

import operator
from pathlib import Path
from typing import Annotated, Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from src.data.models import ValidationReport
from src.validation.benchmark_checks import run_benchmark_parquet_checks
from src.validation.checks import messages_from_checks, run_metrics_checks, run_structural_checks
from src.validation.llm_diagnostics import generate_diagnostics_summary
from src.validation.world_spec_checks import run_world_spec_checks

Decision = Literal["go", "caution", "stop"]
DEFAULT_BENCHMARK_DIR = Path("synthetic_env/benchmarks/generated_sanity_calibrated")


class ValidationState(TypedDict):
    context: dict[str, Any]
    benchmark_dir: str | None
    enable_llm: bool
    checks: Annotated[list[dict[str, Any]], operator.add]
    issues: Annotated[list[str], operator.add]
    warnings: Annotated[list[str], operator.add]
    benchmark_loaded: bool
    decision: Decision
    diagnostics_summary: str
    diagnostics_source: str


def _partition_checks(checks: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "checks": checks,
        "issues": messages_from_checks(checks, "error"),
        "warnings": messages_from_checks(checks, "warning"),
    }


def structural_node(state: ValidationState) -> dict[str, Any]:
    return _partition_checks(run_structural_checks(state["context"]))


def metrics_node(state: ValidationState) -> dict[str, Any]:
    return _partition_checks(run_metrics_checks(state["context"]))


def benchmark_node(state: ValidationState) -> dict[str, Any]:
    experiment_id = state["context"]["experiment"].experiment_id
    benchmark_dir = Path(state["benchmark_dir"] or DEFAULT_BENCHMARK_DIR)
    checks, loaded = run_benchmark_parquet_checks(benchmark_dir, experiment_id)
    result = _partition_checks(checks)
    result["benchmark_loaded"] = loaded
    return result


def world_spec_node(state: ValidationState) -> dict[str, Any]:
    experiment_id = state["context"]["experiment"].experiment_id
    benchmark_dir = Path(state["benchmark_dir"] or DEFAULT_BENCHMARK_DIR)
    checks = run_world_spec_checks(state["context"], benchmark_dir=benchmark_dir)
    return _partition_checks(checks)


def decision_node(state: ValidationState) -> dict[str, Any]:
    errors = state["issues"]
    warnings = state["warnings"]
    if len(errors) >= 2:
        decision: Decision = "stop"
    elif errors or warnings:
        decision = "caution"
    else:
        decision = "go"
    return {"decision": decision}


def llm_diagnostics_node(state: ValidationState) -> dict[str, Any]:
    summary, source = generate_diagnostics_summary(
        decision=state["decision"],
        issues=state["issues"],
        warnings=state["warnings"],
        checks=state["checks"],
        use_llm=state["enable_llm"],
    )
    return {"diagnostics_summary": summary, "diagnostics_source": source}


def build_validation_graph():
    workflow = StateGraph(ValidationState)
    workflow.add_node("structural", structural_node)
    workflow.add_node("metrics", metrics_node)
    workflow.add_node("benchmark", benchmark_node)
    workflow.add_node("world_spec", world_spec_node)
    workflow.add_node("decide", decision_node)
    workflow.add_node("llm_diagnostics", llm_diagnostics_node)
    workflow.add_edge(START, "structural")
    workflow.add_edge("structural", "metrics")
    workflow.add_edge("metrics", "benchmark")
    workflow.add_edge("benchmark", "world_spec")
    workflow.add_edge("world_spec", "decide")
    workflow.add_edge("decide", "llm_diagnostics")
    workflow.add_edge("llm_diagnostics", END)
    return workflow.compile()


class ValidationAgent:
    """Skill 2 agent: context checks, benchmark parquets, world-spec warnings, optional LLM summary."""

    def __init__(
        self,
        benchmark_dir: Path | str | None = None,
        enable_llm: bool | None = None,
    ) -> None:
        self._benchmark_dir = Path(benchmark_dir) if benchmark_dir else None
        self._enable_llm = enable_llm
        self._graph = build_validation_graph()

    def run(self, context: dict) -> dict[str, Any]:
        benchmark_dir = context.get("benchmark_dir") or self._benchmark_dir
        enable_llm = context.get("enable_llm", self._enable_llm)
        if enable_llm is None:
            enable_llm = False

        final_state = self._graph.invoke(
            {
                "context": context,
                "benchmark_dir": str(benchmark_dir) if benchmark_dir else None,
                "enable_llm": bool(enable_llm),
                "checks": [],
                "issues": [],
                "warnings": [],
                "benchmark_loaded": False,
                "decision": "go",
                "diagnostics_summary": "",
                "diagnostics_source": "template",
            }
        )
        report = ValidationReport(
            decision=final_state["decision"],
            issues=final_state["issues"],
            warnings=final_state["warnings"],
            checks=final_state["checks"],
            benchmark_loaded=final_state["benchmark_loaded"],
            diagnostics_summary=final_state["diagnostics_summary"],
            diagnostics_source=final_state["diagnostics_source"],
        )
        return report.model_dump()
