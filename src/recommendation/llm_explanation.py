"""Optional LLM explanation for top recommendation."""

from __future__ import annotations

import json
import os
from typing import Any


def _template_explanation(top: dict[str, Any] | None, ranked: list[dict[str, Any]], warnings: list[str]) -> str:
    if not top:
        return "No candidates were available to recommend. Generate experiment candidates before ranking."

    components = top.get("score_components", {})
    lines = [
        f"Recommended next test: {top.get('candidate_name', 'unknown')}.",
        f"Score {top.get('score')} (rank 1 of {len(ranked)}).",
        (
            "Drivers: "
            f"retention={components.get('retention')}, "
            f"variance_penalty=-{components.get('variance_penalty')}, "
            f"uncertainty_bonus=+{components.get('uncertainty_bonus')}."
        ),
        f"Rationale: {top.get('rationale', 'n/a')}",
        f"Expected tradeoff: {top.get('expected_tradeoff', 'n/a')}",
    ]
    if warnings:
        lines.append("Warnings: " + "; ".join(warnings))
    return "\n".join(lines)


def generate_recommendation_explanation(
    top_recommendation: dict[str, Any] | None,
    ranked_candidates: list[dict[str, Any]],
    evaluation: dict[str, Any],
    warnings: list[str],
    *,
    use_llm: bool | None = None,
) -> tuple[str, str]:
    """Return (explanation, source) where source is 'llm' or 'template'."""
    if use_llm is None:
        from src.llm.client import is_llm_configured

        use_llm = is_llm_configured()

    if not use_llm or not top_recommendation:
        return _template_explanation(top_recommendation, ranked_candidates, warnings), "template"

    try:
        from langchain_core.messages import HumanMessage, SystemMessage

        from src.llm.client import get_chat_llm

        llm = get_chat_llm(model_env="RECOMMENDATION_LLM_MODEL", default_model="gpt-4o-mini")
    except (ImportError, RuntimeError):
        return _template_explanation(top_recommendation, ranked_candidates, warnings), "template"

    payload = {
        "top_recommendation": top_recommendation,
        "ranked_candidates": ranked_candidates[:5],
        "evaluation": evaluation,
        "warnings": warnings,
    }
    messages = [
        SystemMessage(
            content=(
                "You are an experimentation strategist. Explain the top-ranked next test "
                "in 3-5 sentences for a growth PM. Reference score components and tradeoffs. "
                "Do not invent metrics not present in the payload."
            )
        ),
        HumanMessage(content=f"Recommendation payload:\n{json.dumps(payload, default=str)}"),
    ]
    response = llm.invoke(messages)
    content = response.content if isinstance(response.content, str) else str(response.content)
    return content.strip(), "llm"
