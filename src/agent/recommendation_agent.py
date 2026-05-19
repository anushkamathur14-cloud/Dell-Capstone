"""LangGraph recommendation agent: deterministic skill rank + optional LLM tool loop."""

from __future__ import annotations

import operator
import os
from typing import Annotated, Any, Optional, TypedDict

from langgraph.graph import END, START, StateGraph

from src.agent.llm_tool_loop import run_recommendation_tool_loop
from src.agent.tools.registry import get_skill_registry
from src.data.models import RecommendationCandidate, RecommendationReport
from src.recommendation.scoring import DEFAULT_UNCERTAINTY_WEIGHT, DEFAULT_VARIANCE_LAMBDA


class RecommendationState(TypedDict):
    candidates: list[Any]
    evaluation: dict[str, Any]
    context: Optional[dict[str, Any]]
    enable_llm: bool
    enable_llm_loop: bool
    variance_lambda: float
    uncertainty_weight: float
    warnings: Annotated[list[str], operator.add]
    scored_candidates: list[dict[str, Any]]
    ranked_candidates: list[dict[str, Any]]
    canonical_ranked_candidates: list[dict[str, Any]]
    top_recommendation: Optional[dict[str, Any]]
    pending_revisions: list[dict[str, Any]]
    llm_loop_iterations: int
    explanation: str
    explanation_source: str
    ranking_method: str


def prepare_node(state: RecommendationState) -> dict[str, Any]:
    return get_skill_registry().recommendation.run_prepare(state["candidates"], state["evaluation"])


def score_node(state: RecommendationState) -> dict[str, Any]:
    return get_skill_registry().recommendation.run_score(
        state["candidates"],
        state["evaluation"],
        variance_lambda=state["variance_lambda"],
        uncertainty_weight=state["uncertainty_weight"],
    )


def rank_node(state: RecommendationState) -> dict[str, Any]:
    ranked = get_skill_registry().recommendation.run_rank(state["scored_candidates"])
    return {
        **ranked,
        "canonical_ranked_candidates": list(ranked["ranked_candidates"]),
    }


def llm_tool_loop_node(state: RecommendationState) -> dict[str, Any]:
    loop_state = {
        "candidates": state["candidates"],
        "evaluation": state["evaluation"],
        "variance_lambda": state["variance_lambda"],
        "uncertainty_weight": state["uncertainty_weight"],
        "warnings": state["warnings"],
        "scored_candidates": state["scored_candidates"],
        "ranked_candidates": state["ranked_candidates"],
        "top_recommendation": state["top_recommendation"],
    }
    return run_recommendation_tool_loop(
        registry=get_skill_registry(),
        loop_state=loop_state,
        enable=state["enable_llm_loop"],
    )


def explain_node(state: RecommendationState) -> dict[str, Any]:
    return get_skill_registry().recommendation.run_explain(
        top_recommendation=state["top_recommendation"],
        ranked_candidates=state["canonical_ranked_candidates"] or state["ranked_candidates"],
        evaluation=state["evaluation"],
        warnings=state["warnings"],
        enable_llm=state["enable_llm"],
    )


def build_recommendation_graph():
    workflow = StateGraph(RecommendationState)
    workflow.add_node("prepare", prepare_node)
    workflow.add_node("score", score_node)
    workflow.add_node("rank", rank_node)
    workflow.add_node("llm_tool_loop", llm_tool_loop_node)
    workflow.add_node("explain", explain_node)
    workflow.add_edge(START, "prepare")
    workflow.add_edge("prepare", "score")
    workflow.add_edge("score", "rank")
    workflow.add_edge("rank", "llm_tool_loop")
    workflow.add_edge("llm_tool_loop", "explain")
    workflow.add_edge("explain", END)
    return workflow.compile()


class RecommendationAgent:
    """Skill 5 deep agent: canonical lift_aware_v1 + up to 3 LLM tool iterations."""

    def __init__(
        self,
        enable_llm: Optional[bool] = None,
        enable_llm_loop: Optional[bool] = None,
        variance_lambda: float = DEFAULT_VARIANCE_LAMBDA,
        uncertainty_weight: float = DEFAULT_UNCERTAINTY_WEIGHT,
    ) -> None:
        self._enable_llm = enable_llm
        self._enable_llm_loop = enable_llm_loop
        self._variance_lambda = variance_lambda
        self._uncertainty_weight = uncertainty_weight
        self._graph = build_recommendation_graph()

    def run(
        self,
        candidates: list[RecommendationCandidate] | list[dict[str, Any]],
        evaluation: dict[str, Any],
        context: Optional[dict[str, Any]] = None,
    ) -> dict[str, Any]:
        enable_llm = evaluation.get("enable_llm", self._enable_llm)
        if enable_llm is None:
            enable_llm = False
        enable_llm_loop = evaluation.get("enable_llm_loop", self._enable_llm_loop)
        if enable_llm_loop is None:
            enable_llm_loop = os.getenv("ENABLE_RECOMMENDATION_LLM_LOOP", "false").lower() in {
                "1",
                "true",
                "yes",
            }

        variance_lambda = float(evaluation.get("variance_lambda", self._variance_lambda))
        uncertainty_weight = float(evaluation.get("uncertainty_weight", self._uncertainty_weight))

        final_state = self._graph.invoke(
            {
                "candidates": candidates,
                "evaluation": evaluation,
                "context": context,
                "enable_llm": bool(enable_llm),
                "enable_llm_loop": bool(enable_llm_loop),
                "variance_lambda": variance_lambda,
                "uncertainty_weight": uncertainty_weight,
                "warnings": [],
                "scored_candidates": [],
                "ranked_candidates": [],
                "canonical_ranked_candidates": [],
                "top_recommendation": None,
                "pending_revisions": [],
                "llm_loop_iterations": 0,
                "explanation": "",
                "explanation_source": "template",
                "ranking_method": "lift_aware_v1",
            }
        )

        canonical = final_state["canonical_ranked_candidates"] or final_state["ranked_candidates"]
        report = RecommendationReport(
            ranking_method=final_state["ranking_method"],
            top_recommendation=canonical[0] if canonical else final_state["top_recommendation"],
            ranked_candidates=canonical,
            canonical_ranked_candidates=canonical,
            explanation=final_state["explanation"],
            explanation_source=final_state["explanation_source"],
            warnings=final_state["warnings"],
            pending_revisions=final_state.get("pending_revisions") or [],
            llm_loop_iterations=int(final_state.get("llm_loop_iterations") or 0),
        )
        return report.model_dump()
