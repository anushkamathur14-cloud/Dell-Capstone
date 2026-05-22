"""Experiment generation subagent (Azure standard) — schema-validated proposals."""

from __future__ import annotations

import json
import re
from typing import Any

from src.data.models import RecommendationCandidate
from src.llm.azure_factory import get_azure_chat_model
from src.prompts.loader import load_prompt


class GenerationAgent:
    def run(self, context: dict[str, Any], evaluation: dict[str, Any]) -> list[dict[str, Any]]:
        llm = get_azure_chat_model("generation")
        if llm is None:
            return _stub_proposals(context, evaluation)

        experiment = context["experiment"]
        metrics = context.get("metrics") or []
        arms = context.get("arms") or []
        payload = {
            "experiment_id": experiment.experiment_id,
            "objective": experiment.objective,
            "evaluation": evaluation,
            "arms": [
                {"arm_id": a.arm_id, "parameters": a.structured_parameters_json} for a in arms[:6]
            ],
            "metrics": [
                {
                    "arm_id": m.arm_id,
                    "retention": m.retention,
                    "conversion": m.conversion,
                    "sample_size": m.sample_size,
                }
                for m in metrics[:6]
            ],
        }
        from langchain_core.messages import HumanMessage, SystemMessage

        response = llm.invoke(
            [
                SystemMessage(content=load_prompt("generation/system.md")),
                HumanMessage(content=json.dumps(payload, default=str)),
            ]
        )
        text = response.content if isinstance(response.content, str) else str(response.content)
        return _parse_proposals(text, context, evaluation)


def _stub_proposals(context: dict[str, Any], evaluation: dict[str, Any]) -> list[dict[str, Any]]:
    experiment_id = context["experiment"].experiment_id
    baseline_metric = context["metrics"][0] if context["metrics"] else None
    signal = (evaluation.get("ranked_directions") or ["baseline"])[0]
    row = RecommendationCandidate(
        candidate_name=f"{experiment_id}-llm-fallback",
        parameter_changes={"onboarding_copy": "value_prop_v2"},
        rationale="LLM generation unavailable; fallback proposal.",
        expected_tradeoff="n/a",
        target_segment="aggregate",
        implementation_notes="Check Azure config.",
        signal_from_eval=signal,
        metric_stub={
            "retention": baseline_metric.retention if baseline_metric else None,
            "conversion": baseline_metric.conversion if baseline_metric else None,
        },
    ).model_dump()
    row["source"] = "generation_agent_fallback"
    return [row]


def _parse_proposals(text: str, context: dict, evaluation: dict) -> list[dict[str, Any]]:
    match = re.search(r"\[[\s\S]*\]", text)
    if not match:
        return _stub_proposals(context, evaluation)
    try:
        raw = json.loads(match.group())
    except json.JSONDecodeError:
        return _stub_proposals(context, evaluation)
    out: list[dict[str, Any]] = []
    signal = (evaluation.get("ranked_directions") or ["baseline"])[0]
    for item in raw[:3]:
        if not isinstance(item, dict):
            continue
        try:
            cand = RecommendationCandidate(
                candidate_name=str(item.get("candidate_name") or "proposal"),
                parameter_changes=item.get("parameter_changes") or {},
                rationale=str(item.get("rationale") or ""),
                expected_tradeoff=str(item.get("expected_tradeoff") or "n/a"),
                target_segment=str(item.get("target_segment") or "aggregate"),
                implementation_notes=str(item.get("implementation_notes") or ""),
                signal_from_eval=str(item.get("signal_from_eval") or signal),
                metric_stub=item.get("metric_stub") or {},
            )
            row = cand.model_dump()
            row["source"] = "generation_agent"
            out.append(row)
        except Exception:
            continue
    return out or _stub_proposals(context, evaluation)
