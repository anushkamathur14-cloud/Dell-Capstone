"""Agent orchestrator for the MVP workflow."""

from dataclasses import dataclass
from typing import Any

from src.agent.runtime_options import (
    recommendation_runtime_options,
    retrieval_benchmark_dir,
    validation_runtime_options,
)
from src.agent.recommendation_agent import RecommendationAgent
from src.agent.validation_agent import ValidationAgent
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
    validation_report: dict[str, Any]
    evaluation: dict[str, Any]
    recommendation: dict[str, Any]
    data_source: str


class AdaptiveExperimentationOrchestrator:
    """Coordinates modular skills in a recommendation-first sequence."""

    def __init__(self) -> None:
        benchmark_dir = retrieval_benchmark_dir()
        self.retrieval = RetrievalSkill(benchmark_dir=benchmark_dir)
        self.validation = ValidationSkill(agent=ValidationAgent(benchmark_dir=benchmark_dir))
        self.evaluator = CausalEvaluationSkill()
        self.generator = ExperimentGenerationSkill()
        self.recommender = RecommendationSkill()

    def run(self, objective: str, experiment_id: str) -> OrchestrationResult:
        context = self.retrieval.run(objective=objective, experiment_id=experiment_id)
        context.update(validation_runtime_options())

        validation_report = self.validation.run(context)
        if validation_report["decision"] == "stop":
            raise ValueError("Validation failed: pipeline halted.")

        evaluation = self.evaluator.run(context)
        evaluation.update(recommendation_runtime_options())

        candidates = self.generator.run(context=context, evaluation=evaluation)
        recommendation = self.recommender.run(
            candidates=candidates,
            evaluation=evaluation,
            context=context,
        )

        return OrchestrationResult(
            schema_version="v1.0",
            experiment=context["experiment"],
            memory=context["memory"],
            metrics=context["metrics"],
            validation_report=validation_report,
            evaluation=evaluation,
            recommendation=recommendation,
            data_source=context.get("data_source", "unknown"),
        )
