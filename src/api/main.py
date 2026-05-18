"""FastAPI app stub."""

import os

from fastapi import FastAPI

from src.agent.orchestrator import AdaptiveExperimentationOrchestrator
from src.agent.recommendation_agent import RecommendationAgent
from src.agent.validation_agent import DEFAULT_BENCHMARK_DIR, ValidationAgent
from src.skills.causal_evaluation import CausalEvaluationSkill
from src.skills.experiment_generation import ExperimentGenerationSkill
from src.skills.retrieval import RetrievalSkill

app = FastAPI(title="Adaptive Experimentation Agent", version="0.1.0")


@app.get("/")
def root() -> dict:
    return {"service": "adaptive-experimentation-agent", "mode": "mvp-starter"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


def _recommendation_runtime_options() -> dict:
    enable_llm = os.getenv("ENABLE_RECOMMENDATION_LLM", "false").lower() in {"1", "true", "yes"}
    return {
        "enable_llm": enable_llm,
        "variance_lambda": float(os.getenv("RECOMMENDATION_VARIANCE_LAMBDA", "0.2")),
        "uncertainty_weight": float(os.getenv("RECOMMENDATION_UNCERTAINTY_WEIGHT", "0.2")),
    }


def _validation_runtime_options() -> dict:
    benchmark_dir = os.getenv("BENCHMARK_DATA_DIR", str(DEFAULT_BENCHMARK_DIR))
    enable_llm = os.getenv("ENABLE_VALIDATION_LLM", "false").lower() in {"1", "true", "yes"}
    return {"benchmark_dir": benchmark_dir, "enable_llm": enable_llm}


@app.post("/validate/{experiment_id}")
def validate(experiment_id: str, objective: str = "day7_retention") -> dict:
    context = RetrievalSkill().run(objective=objective, experiment_id=experiment_id)
    context.update(_validation_runtime_options())
    return ValidationAgent(
        benchmark_dir=context["benchmark_dir"],
        enable_llm=context["enable_llm"],
    ).run(context)


@app.post("/recommend/{experiment_id}")
def recommend(experiment_id: str, objective: str = "day7_retention") -> dict:
    context = RetrievalSkill().run(objective=objective, experiment_id=experiment_id)
    evaluation = CausalEvaluationSkill().run(context)
    evaluation.update(_recommendation_runtime_options())
    candidates = ExperimentGenerationSkill().run(context=context, evaluation=evaluation)
    return RecommendationAgent(
        enable_llm=evaluation.get("enable_llm"),
        variance_lambda=evaluation.get("variance_lambda", 0.2),
        uncertainty_weight=evaluation.get("uncertainty_weight", 0.2),
    ).run(candidates=candidates, evaluation=evaluation, context=context)


@app.post("/orchestrate/{experiment_id}")
def orchestrate(experiment_id: str, objective: str) -> dict:
    orchestrator = AdaptiveExperimentationOrchestrator()
    result = orchestrator.run(objective=objective, experiment_id=experiment_id)
    return {
        "experiment": result.experiment.model_dump(),
        "memory": result.memory.model_dump(),
        "metrics": [metric.model_dump() for metric in result.metrics],
        "validation_report": result.validation_report,
        "recommendation": result.recommendation,
    }
