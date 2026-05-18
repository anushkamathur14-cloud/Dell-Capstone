"""LangGraph validation agent for experiment context quality gating."""

from __future__ import annotations

import operator
from typing import Annotated, Any, Literal, TypedDict

from langgraph.graph import END, START, StateGraph

from src.data.models import ValidationReport
from src.validation.checks import run_metrics_checks, run_structural_checks

Decision = Literal["go", "caution", "stop"]


class ValidationState(TypedDict):
    context: dict[str, Any]
    checks: Annotated[list[dict[str, Any]], operator.add]
    issues: Annotated[list[str], operator.add]
    decision: Decision


def _failed_issues(checks: list[dict[str, Any]]) -> list[str]:
    return [check["message"] for check in checks if not check["passed"]]


def structural_node(state: ValidationState) -> dict[str, Any]:
    checks = run_structural_checks(state["context"])
    return {"checks": checks, "issues": _failed_issues(checks)}


def metrics_node(state: ValidationState) -> dict[str, Any]:
    checks = run_metrics_checks(state["context"])
    return {"checks": checks, "issues": _failed_issues(checks)}


def decision_node(state: ValidationState) -> dict[str, Any]:
    issues = state["issues"]
    if len(issues) >= 2:
        decision: Decision = "stop"
    elif issues:
        decision = "caution"
    else:
        decision = "go"
    return {"decision": decision}


def build_validation_graph():
    workflow = StateGraph(ValidationState)
    workflow.add_node("structural", structural_node)
    workflow.add_node("metrics", metrics_node)
    workflow.add_node("decide", decision_node)
    workflow.add_edge(START, "structural")
    workflow.add_edge("structural", "metrics")
    workflow.add_edge("metrics", "decide")
    workflow.add_edge("decide", END)
    return workflow.compile()


class ValidationAgent:
    """Skill 2 agent: structural + metrics checks with go/caution/stop output."""

    def __init__(self) -> None:
        self._graph = build_validation_graph()

    def run(self, context: dict) -> dict[str, Any]:
        final_state = self._graph.invoke(
            {
                "context": context,
                "checks": [],
                "issues": [],
                "decision": "go",
            }
        )
        report = ValidationReport(
            decision=final_state["decision"],
            issues=final_state["issues"],
            checks=final_state["checks"],
        )
        return report.model_dump()
