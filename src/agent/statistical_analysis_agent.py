"""Post-experiment statistical analysis agent (runs after experiment completes)."""

from __future__ import annotations

from typing import Any, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from src.agent.tools.registry import get_skill_registry


class StatisticalAnalysisState(TypedDict):
    context: dict[str, Any]
    evaluation: dict[str, Any]
    validation_report: Optional[dict[str, Any]]
    report: dict[str, Any]


def analysis_node(state: StatisticalAnalysisState) -> dict[str, Any]:
    report = get_skill_registry().invoke(
        "statistical_analysis_skill",
        context=state["context"],
        evaluation=state.get("evaluation"),
        validation_report=state.get("validation_report"),
    )
    return {"report": report}


def build_statistical_analysis_graph():
    workflow = StateGraph(StatisticalAnalysisState)
    workflow.add_node("analyze", analysis_node)
    workflow.add_edge(START, "analyze")
    workflow.add_edge("analyze", END)
    return workflow.compile()


class StatisticalAnalysisAgent:
    """Deep agent with a single skill-backed node."""

    def __init__(self) -> None:
        self._graph = build_statistical_analysis_graph()

    def run(
        self,
        context: dict[str, Any],
        evaluation: Optional[dict[str, Any]] = None,
        validation_report: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        final = self._graph.invoke(
            {
                "context": context,
                "evaluation": evaluation or {},
                "validation_report": validation_report,
                "report": {},
            }
        )
        return final["report"]
