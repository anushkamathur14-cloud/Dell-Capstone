"""Experiment generation — LLM subagent when ENABLE_GENERATION_AGENT=true."""

from __future__ import annotations

from typing import Any

from src.agents.generation_agent import GenerationAgent
from src.config.settings import get_settings
from src.data.models import RecommendationCandidate


class ExperimentGenerationSkill:
    def __init__(self, agent: GenerationAgent | None = None) -> None:
        self._agent = agent or GenerationAgent()

    def run(self, context: dict, evaluation: dict) -> list[dict[str, Any]]:
        if not get_settings().enable_generation_agent:
            experiment_id = context["experiment"].experiment_id
            baseline_metric = context["metrics"][0] if context["metrics"] else None
            return [
                RecommendationCandidate(
                    candidate_name=f"{experiment_id}-candidate-1",
                    parameter_changes={"onboarding_copy": "value_prop_v2"},
                    rationale="Stub proposal (generation agent disabled).",
                    expected_tradeoff="n/a",
                    target_segment="new_users",
                    implementation_notes="Enable ENABLE_GENERATION_AGENT for LLM proposals.",
                    signal_from_eval=(evaluation.get("ranked_directions") or ["baseline"])[0],
                    metric_stub={
                        "retention": baseline_metric.retention if baseline_metric else None,
                        "variance": baseline_metric.variance if baseline_metric else None,
                    },
                ).model_dump()
            ]
        return self._agent.run(context, evaluation)
