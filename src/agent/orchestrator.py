"""Agent orchestrator stub for the MVP workflow."""

from dataclasses import dataclass
from typing import Any

from src.data.models import Experiment, ExperimentMemory, MetricsSummary
from src.skills.causal_evaluation import CausalEvaluationSkill
from src.skills.experiment_generation import ExperimentGenerationSkill
from src.skills.recommendation import RecommendationSkill
from src.skills.retrieval import RetrievalSkill
from src.skills.validation import ValidationSkill


@dataclass
class OrchestrationResult:
    schema_version: str
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
        context = self.retrieval.run(objective=objective, experiment_id=experiment_id)
        validation_report = self.validation.run(context)

        if validation_report["decision"] == "stop":
            raise ValueError("Validation failed: pipeline halted.")

        evaluation = self.evaluator.run(context)
        candidates = self.generator.run(context=context, evaluation=evaluation)
        recommendation = self.recommender.run(candidates=candidates, evaluation=evaluation)

        return OrchestrationResult(
            schema_version="v1.0",
            experiment=context["experiment"],
            memory=context["memory"],
            metrics=context["metrics"],
            recommendation=recommendation,
        )
