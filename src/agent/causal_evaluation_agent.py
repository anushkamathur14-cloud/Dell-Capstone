"""LangGraph causal agent — all steps invoke CausalEvaluationSkill tools (4A)."""

from __future__ import annotations

import os
from typing import Any, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from src.agent.tools.registry import get_skill_registry


class CausalEvaluationState(TypedDict):
    context: dict[str, Any]
    enable_sandbox: bool
    programmatic: dict[str, Any]
    experiment_design: dict[str, Any]
    evaluation: dict[str, Any]


def programmatic_node(state: CausalEvaluationState) -> dict[str, Any]:
    programmatic = get_skill_registry().invoke("causal_evaluation_skill", context=state["context"])
    return {"programmatic": programmatic, "evaluation": programmatic}


def design_node(state: CausalEvaluationState) -> dict[str, Any]:
    design = get_skill_registry().invoke(
        "causal_design_experiment_skill",
        context=state["context"],
        evaluation=state["evaluation"],
    )
    return {"experiment_design": design}


def sandbox_node(state: CausalEvaluationState) -> dict[str, Any]:
    if not state.get("enable_sandbox", True):
        return {"evaluation": state["evaluation"]}
    merged = get_skill_registry().invoke(
        "causal_sandbox_analysis_skill",
        context=state["context"],
        evaluation=state["evaluation"],
    )
    merged["experiment_design"] = state.get("experiment_design")
    return {"evaluation": merged}


def build_causal_evaluation_graph():
    workflow = StateGraph(CausalEvaluationState)
    workflow.add_node("programmatic", programmatic_node)
    workflow.add_node("design", design_node)
    workflow.add_node("sandbox", sandbox_node)
    workflow.add_edge(START, "programmatic")
    workflow.add_edge("programmatic", "design")
    workflow.add_edge("design", "sandbox")
    workflow.add_edge("sandbox", END)
    return workflow.compile()


class CausalEvaluationAgent:
    def __init__(self) -> None:
        self._graph = build_causal_evaluation_graph()

    def run(self, context: dict[str, Any]) -> dict[str, Any]:
        enable_sandbox = os.getenv("ENABLE_CAUSAL_SANDBOX", "true").lower() in {"1", "true", "yes"}
        final = self._graph.invoke(
            {
                "context": context,
                "enable_sandbox": enable_sandbox,
                "programmatic": {},
                "experiment_design": {},
                "evaluation": {},
            }
        )
        return final["evaluation"]
