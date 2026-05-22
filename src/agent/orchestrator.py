"""Agent orchestrator: canonical v1 deterministic path (thin, sequential).

Canonical wiring (benchmarked path):
retrieval → validation → causal evaluation → recommendation

Experiment generation stays a separate module / trace name for Phase 2; it is **not**
invoked here. Ranking inputs are assembled from retrieval context — see ``ranking_inputs``.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.agent.ranking_inputs import ranking_candidates_from_context
from src.config.settings import get_settings
from src.data.models import Experiment, ExperimentMemory, MetricsSummary
from src.agent.traced_steps import (
    run_causal_evaluation_skill,
    run_experiment_generation_skill,
    run_recommendation_skill,
    run_retrieval_skill,
    run_validation_skill,
)
from src.skills.causal_evaluation import CausalEvaluationSkill
from src.skills.experiment_generation import ExperimentGenerationSkill  # Slice D stub; unused in canonical v1 path
from src.skills.recommendation import RecommendationSkill
from src.skills.retrieval import RetrievalSkill
from src.skills.validation import ValidationSkill


@dataclass
class OrchestrationResult:
    """Bundle from canonical v1 runs (after validation ``go``/``caution`` — ``stop`` raises)."""

    schema_version: str
    experiment: Experiment
    memory: ExperimentMemory
    metrics: list[MetricsSummary]
    validation_report: dict[str, Any]
    evaluation: dict[str, Any]
    candidates: list[dict[str, Any]]
    recommendation: dict[str, Any]


class AdaptiveExperimentationOrchestrator:
    """Owns synchronous canonical v1: retrieval → validation → causal evaluation → recommendation.

    ``self.generator`` is retained as a Slice D anchor (callable elsewhere / tests); the
    default ``run`` path does **not** call it. LangSmith: ``experiment_generation_skill``
    trace does not appear in canonical runs until Phase 2.
    """

    def __init__(self) -> None:
        self.retrieval = RetrievalSkill()
        self.validation = ValidationSkill()
        self.evaluator = CausalEvaluationSkill()
        self.generator = ExperimentGenerationSkill()  # Deferred from canonical orchestration (Slice D).
        self.recommender = RecommendationSkill()

    def run(self, objective: str, experiment_id: str) -> OrchestrationResult:
        context = run_retrieval_skill(self.retrieval, objective=objective, experiment_id=experiment_id)
        settings = get_settings()
        context["benchmark_dir"] = context.get("benchmark_dir") or settings.benchmark_data_dir
        context["enable_llm"] = settings.enable_validation_llm
        context["use_causal_agent_loop"] = settings.enable_causal_agent_loop

        validation_report = run_validation_skill(self.validation, context)

        if validation_report["decision"] == "stop":
            raise ValueError("Validation failed: pipeline halted.")

        evaluation = run_causal_evaluation_skill(self.evaluator, context)
        signal = (evaluation.get("ranked_directions") or ["baseline"])[0]
        ranking_inputs = ranking_candidates_from_context(context)
        for item in ranking_inputs:
            item["signal_from_eval"] = signal

        candidates: list[dict[str, Any]] = list(ranking_inputs)
        if settings.enable_generation_agent:
            proposals = run_experiment_generation_skill(
                self.generator, context=context, evaluation=evaluation
            )
            seen = {c["candidate_name"] for c in candidates}
            for proposal in proposals:
                if proposal["candidate_name"] not in seen:
                    candidates.append(proposal)
                    seen.add(proposal["candidate_name"])

        recommendation = run_recommendation_skill(
            self.recommender, candidates=candidates, evaluation=evaluation
        )

        return OrchestrationResult(
            schema_version="v1.0",
            experiment=context["experiment"],
            memory=context["memory"],
            metrics=context["metrics"],
            validation_report=validation_report,
            evaluation=evaluation,
            candidates=candidates,
            recommendation=recommendation,
        )
