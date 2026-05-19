"""LangGraph validation agent — nodes invoke ValidationSkill steps only (4A)."""

from __future__ import annotations

import operator
from pathlib import Path
from typing import Annotated, Any, Literal, Optional, TypedDict, Union

from langgraph.graph import END, START, StateGraph

from src.agent.tools.registry import get_skill_registry
from src.data.models import ValidationReport
from src.skills.validation import DEFAULT_BENCHMARK_DIR

Decision = Literal["go", "caution", "stop"]


class ValidationState(TypedDict):
    context: dict[str, Any]
    benchmark_dir: Optional[str]
    enable_llm: bool
    checks: Annotated[list[dict[str, Any]], operator.add]
    issues: Annotated[list[str], operator.add]
    warnings: Annotated[list[str], operator.add]
    benchmark_loaded: bool
    decision: Decision
    diagnostics_summary: str
    diagnostics_source: str


def structural_node(state: ValidationState) -> dict[str, Any]:
    return get_skill_registry().validation.run_structural(state["context"])


def metrics_node(state: ValidationState) -> dict[str, Any]:
    return get_skill_registry().validation.run_metrics(state["context"])


def benchmark_node(state: ValidationState) -> dict[str, Any]:
    return get_skill_registry().validation.run_benchmark(
        state["context"],
        benchmark_dir=state.get("benchmark_dir"),
    )


def world_spec_node(state: ValidationState) -> dict[str, Any]:
    return get_skill_registry().validation.run_world_spec(
        state["context"],
        benchmark_dir=state.get("benchmark_dir"),
    )


def decision_node(state: ValidationState) -> dict[str, Any]:
    return get_skill_registry().validation.run_decide(state["issues"], state["warnings"])


def llm_diagnostics_node(state: ValidationState) -> dict[str, Any]:
    return get_skill_registry().validation.run_diagnostics(
        state["decision"],
        state["issues"],
        state["warnings"],
        state["checks"],
        enable_llm=state["enable_llm"],
    )


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
    """Deep agent: each node delegates to ValidationSkill."""

    def __init__(
        self,
        benchmark_dir: Optional[Union[Path, str]] = None,
        enable_llm: Optional[bool] = None,
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
                "benchmark_dir": str(benchmark_dir) if benchmark_dir else str(DEFAULT_BENCHMARK_DIR),
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
