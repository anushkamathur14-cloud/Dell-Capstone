"""Hybrid agent-in-the-loop: LLM issues programmatic tool calls (max 3 iterations)."""

from __future__ import annotations

import json
import os
import uuid
from typing import Any, Optional

from src.agent.tools.registry import SkillRegistry, get_skill_registry
from src.data.models import RecommendationRevision

MAX_LLM_ITERATIONS = 3

RECOMMENDATION_LOOP_TOOLS = (
    "recommendation_score_skill",
    "recommendation_rank_skill",
)


def _parse_tool_call(raw: str) -> Optional[dict[str, Any]]:
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if isinstance(data, dict) and "tool" in data:
        return data
    return None


def _llm_next_tool_call(
    *,
    catalog: str,
    state_snapshot: dict[str, Any],
    iteration: int,
) -> Optional[dict[str, Any]]:
    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        return None
    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI
    except ImportError:
        return None

    model_name = os.getenv("RECOMMENDATION_LLM_MODEL", "gpt-4o-mini")
    llm = ChatOpenAI(model=model_name, temperature=0, api_key=api_key)
    system = (
        "You assist with experiment recommendation review. "
        f"Respond with ONE JSON object only, max {MAX_LLM_ITERATIONS} steps total.\n"
        "Allowed tools:\n"
        f"{catalog}\n"
        'To finish: {"tool": "finish", "rationale": "..."}\n'
        'To propose a re-rank for human approval: {"tool": "propose_revision", "rationale": "...", '
        '"proposed_ranked_candidates": [...]}\n'
        'To re-score: {"tool": "recommendation_score_skill", "args": {}}\n'
        'To re-rank: {"tool": "recommendation_rank_skill", "args": {}}\n'
        "Do not replace canonical ranking silently."
    )
    human = json.dumps({"iteration": iteration, "state": state_snapshot}, default=str)[:6000]
    response = llm.invoke([SystemMessage(content=system), HumanMessage(content=human)])
    content = getattr(response, "content", str(response))
    return _parse_tool_call(content)


def run_recommendation_tool_loop(
    *,
    registry: SkillRegistry,
    loop_state: dict[str, Any],
    enable: bool,
) -> dict[str, Any]:
    """Run up to 3 LLM tool iterations; canonical rank stays in loop_state."""
    if not enable:
        return {"pending_revisions": [], "llm_loop_iterations": 0}

    catalog = registry.tool_catalog_for_prompt(list(RECOMMENDATION_LOOP_TOOLS) + ["propose_revision", "finish"])
    pending: list[RecommendationRevision] = []
    iterations = 0

    for iteration in range(MAX_LLM_ITERATIONS):
        snapshot = {
            "top": loop_state.get("top_recommendation"),
            "ranked_count": len(loop_state.get("ranked_candidates") or []),
            "warnings": loop_state.get("warnings"),
        }
        call = _llm_next_tool_call(catalog=catalog, state_snapshot=snapshot, iteration=iteration)
        if not call:
            break
        iterations += 1
        tool = call.get("tool")
        if tool == "finish":
            break
        if tool == "propose_revision":
            pending.append(
                RecommendationRevision(
                    revision_id=str(uuid.uuid4())[:8],
                    tool_name="propose_revision",
                    rationale=str(call.get("rationale", "")),
                    proposed_ranked_candidates=call.get("proposed_ranked_candidates") or [],
                    status="pending_approval",
                )
            )
            continue
        if tool in RECOMMENDATION_LOOP_TOOLS:
            try:
                if tool == "recommendation_score_skill":
                    loop_state.update(
                        registry.recommendation.run_score(
                            candidates=loop_state["candidates"],
                            evaluation=loop_state["evaluation"],
                            variance_lambda=loop_state["variance_lambda"],
                            uncertainty_weight=loop_state["uncertainty_weight"],
                        )
                    )
                elif tool == "recommendation_rank_skill":
                    loop_state.update(registry.recommendation.run_rank(loop_state["scored_candidates"]))
            except Exception:
                break
            continue
        break

    return {
        "pending_revisions": [r.model_dump() for r in pending],
        "llm_loop_iterations": iterations,
        "ranked_candidates": loop_state.get("ranked_candidates"),
        "top_recommendation": loop_state.get("top_recommendation"),
        "scored_candidates": loop_state.get("scored_candidates"),
    }
