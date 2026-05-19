"""FastAPI service for the adaptive experimentation agent."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.agent.orchestrator import AdaptiveExperimentationOrchestrator
from src.agent.recommendation_agent import RecommendationAgent
from src.agent.runtime_options import recommendation_runtime_options, validation_runtime_options
from src.agent.validation_agent import ValidationAgent
from src.skills.causal_evaluation import CausalEvaluationSkill
from src.skills.experiment_generation import ExperimentGenerationSkill
from src.skills.retrieval import RetrievalSkill
from src.retrieval.benchmark_context import resolve_benchmark_dir

app = FastAPI(title="Adaptive Experimentation Agent", version="0.2.0")

_cors_origins = os.getenv("CORS_ALLOW_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in _cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root() -> dict:
    return {"service": "adaptive-experimentation-agent", "mode": "mvp"}


@app.get("/health")
def health() -> dict:
    benchmark_dir = resolve_benchmark_dir()
    parquets_ready = all((benchmark_dir / f"{name}.parquet").exists() for name in (
        "population",
        "experiments",
        "arms",
        "observations",
        "metrics_summary",
    ))
    return {
        "status": "ok",
        "benchmark_data_dir": str(benchmark_dir),
        "benchmark_parquets_ready": parquets_ready,
    }


@app.post("/validate/{experiment_id}")
def validate(experiment_id: str, objective: str = "day7_retention") -> dict:
    context = RetrievalSkill().run(objective=objective, experiment_id=experiment_id)
    context.update(validation_runtime_options())
    return ValidationAgent(
        benchmark_dir=context["benchmark_dir"],
        enable_llm=context["enable_llm"],
    ).run(context)


@app.post("/recommend/{experiment_id}")
def recommend(experiment_id: str, objective: str = "day7_retention") -> dict:
    context = RetrievalSkill().run(objective=objective, experiment_id=experiment_id)
    evaluation = CausalEvaluationSkill().run(context)
    evaluation.update(recommendation_runtime_options())
    candidates = ExperimentGenerationSkill().run(context=context, evaluation=evaluation)
    return RecommendationAgent(
        enable_llm=evaluation.get("enable_llm"),
        variance_lambda=evaluation.get("variance_lambda", 0.2),
        uncertainty_weight=evaluation.get("uncertainty_weight", 0.2),
    ).run(candidates=candidates, evaluation=evaluation, context=context)


@app.post("/orchestrate/{experiment_id}")
def orchestrate(experiment_id: str, objective: str = "improve_retention") -> dict:
    result = AdaptiveExperimentationOrchestrator().run(
        objective=objective,
        experiment_id=experiment_id,
    )
    return {
        "schema_version": result.schema_version,
        "data_source": result.data_source,
        "experiment": result.experiment.model_dump(),
        "memory": result.memory.model_dump(),
        "metrics": [metric.model_dump() for metric in result.metrics],
        "validation_report": result.validation_report,
        "evaluation": result.evaluation,
        "recommendation": result.recommendation,
    }
