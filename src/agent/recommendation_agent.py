"""LangGraph recommendation agent for ranking next-best experiments.

Scores candidates with a lift-aware formula, ranks them, and emits an optional
LLM or template explanation. See docs/recommendation_agent.md.
"""

from __future__ import annotations

import operator
from typing import Annotated, Any, TypedDict

from langgraph.graph import END, START, StateGraph

from src.data.models import RecommendationCandidate, RecommendationReport
from src.recommendation.input_checks import run_input_checks
from src.recommendation.llm_explanation import generate_recommendation_explanation
from src.recommendation.ranking import rank_scored_candidates
from src.recommendation.scoring import (
    DEFAULT_UNCERTAINTY_WEIGHT,
    DEFAULT_VARIANCE_LAMBDA,
    score_candidate,
)


class RecommendationState(TypedDict):
    candidates: list[Any]
    evaluation: dict[str, Any]
    context: dict[str, Any] | None
    enable_llm: bool
    variance_lambda: float
    uncertainty_weight: float
    warnings: Annotated[list[str], operator.add]
    scored_candidates: list[dict[str, Any]]
    ranked_candidates: list[dict[str, Any]]
    top_recommendation: dict[str, Any] | None
    explanation: str
    explanation_source: str
    ranking_method: str


def prepare_node(state: RecommendationState) -> dict[str, Any]:
    warnings = run_input_checks(state["candidates"], state["evaluation"])
    return {"warnings": warnings}


def score_node(state: RecommendationState) -> dict[str, Any]:
    scored = [
        score_candidate(
            candidate,
            state["evaluation"],
            variance_lambda=state["variance_lambda"],
            uncertainty_weight=state["uncertainty_weight"],
        )
        for candidate in state["candidates"]
    ]
    return {"scored_candidates": scored}


def rank_node(state: RecommendationState) -> dict[str, Any]:
    ranked = rank_scored_candidates(state["scored_candidates"])
    top = ranked[0] if ranked else None
    return {"ranked_candidates": ranked, "top_recommendation": top}


def explain_node(state: RecommendationState) -> dict[str, Any]:
    explanation, source = generate_recommendation_explanation(
        top_recommendation=state["top_recommendation"],
        ranked_candidates=state["ranked_candidates"],
        evaluation=state["evaluation"],
        warnings=state["warnings"],
        use_llm=state["enable_llm"],
    )
    return {"explanation": explanation, "explanation_source": source}


def build_recommendation_graph():
    workflow = StateGraph(RecommendationState)
    workflow.add_node("prepare", prepare_node)
    workflow.add_node("score", score_node)
    workflow.add_node("rank", rank_node)
    workflow.add_node("explain", explain_node)
    workflow.add_edge(START, "prepare")
    workflow.add_edge("prepare", "score")
    workflow.add_edge("score", "rank")
    workflow.add_edge("rank", "explain")
    workflow.add_edge("explain", END)
    return workflow.compile()


class RecommendationAgent:
    """Skill 5 agent: score, rank, and explain next-best experiment candidates."""

    def __init__(
        self,
        enable_llm: bool | None = None,
        variance_lambda: float = DEFAULT_VARIANCE_LAMBDA,
        uncertainty_weight: float = DEFAULT_UNCERTAINTY_WEIGHT,
    ) -> None:
        self._enable_llm = enable_llm
        self._variance_lambda = variance_lambda
        self._uncertainty_weight = uncertainty_weight
        self._graph = build_recommendation_graph()

    def run(
        self,
        candidates: list[RecommendationCandidate] | list[dict[str, Any]],
        evaluation: dict[str, Any],
        context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        enable_llm = evaluation.get("enable_llm", self._enable_llm)
        if enable_llm is None:
            enable_llm = False

        variance_lambda = float(evaluation.get("variance_lambda", self._variance_lambda))
        uncertainty_weight = float(evaluation.get("uncertainty_weight", self._uncertainty_weight))

        final_state = self._graph.invoke(
            {
                "candidates": candidates,
                "evaluation": evaluation,
                "context": context,
                "enable_llm": bool(enable_llm),
                "variance_lambda": variance_lambda,
                "uncertainty_weight": uncertainty_weight,
                "warnings": [],
                "scored_candidates": [],
                "ranked_candidates": [],
                "top_recommendation": None,
                "explanation": "",
                "explanation_source": "template",
                "ranking_method": "lift_aware_v1",
            }
        )

        report = RecommendationReport(
            ranking_method=final_state["ranking_method"],
            top_recommendation=final_state["top_recommendation"],
            ranked_candidates=final_state["ranked_candidates"],
            explanation=final_state["explanation"],
            explanation_source=final_state["explanation_source"],
            warnings=final_state["warnings"],
        )
        return report.model_dump()
