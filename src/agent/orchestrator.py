"""Agent orchestrator stub for the MVP workflow."""

from dataclasses import dataclass
from typing import Any

from src.data.models import Experiment, ExperimentMemory, MetricsSummary
from src.agent.traced_steps import (
    run_causal_evaluation_skill,
    run_experiment_generation_skill,
    run_recommendation_skill,
    run_retrieval_skill,
    run_validation_skill,
)
from src.skills.causal_evaluation import CausalEvaluationSkill
from src.skills.experiment_generation import ExperimentGenerationSkill
from src.skills.recommendation import RecommendationSkill
from src.skills.retrieval import RetrievalSkill
from src.skills.validation import ValidationSkill


@dataclass
class OrchestrationResult:
    experiment: Experiment
    memory: ExperimentMemory
    metrics: list[MetricsSummary]
    recommendation: dict[str, Any]


class AdaptiveExperimentationOrchestrator:
    """Coordinates modular skills in a recommendation-first sequence."""

    def __init__(self) -> None:
        self.retrieval = RetrievalSkill()
        self.validation = ValidationSkill()
        self.evaluator = CausalEvaluationSkill()
        self.generator = ExperimentGenerationSkill()
        self.recommender = RecommendationSkill()

    def run(self, objective: str, experiment_id: str) -> OrchestrationResult:
        context = run_retrieval_skill(self.retrieval, objective=objective, experiment_id=experiment_id)
        validation_report = run_validation_skill(self.validation, context)

        if validation_report["decision"] == "stop":
            raise ValueError("Validation failed: pipeline halted.")

        evaluation = run_causal_evaluation_skill(self.evaluator, context)
        candidates = run_experiment_generation_skill(
            self.generator, context=context, evaluation=evaluation
        )
        recommendation = run_recommendation_skill(
            self.recommender, candidates=candidates, evaluation=evaluation
        )

        return OrchestrationResult(
            experiment=context["experiment"],
            memory=context["memory"],
            metrics=context["metrics"],
            recommendation=recommendation,
        )
