"""FastAPI service for the adaptive experimentation agent."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.agent.causal_evaluation_agent import CausalEvaluationAgent
from src.agent.orchestrator import AdaptiveExperimentationOrchestrator
from src.agent.recommendation_agent import RecommendationAgent
from src.agent.runtime_options import (
    causal_runtime_options,
    recommendation_runtime_options,
    validation_runtime_options,
)
from src.agent.statistical_analysis_agent import StatisticalAnalysisAgent
from src.agent.validation_agent import ValidationAgent
from src.skills.experiment_generation import ExperimentGenerationSkill
from src.skills.retrieval import RetrievalSkill
from src.retrieval.benchmark_context import resolve_benchmark_dir

app = FastAPI(title="Adaptive Experimentation Agent", version="0.3.0")

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
    parquets_ready = all(
        (benchmark_dir / f"{name}.parquet").exists()
        for name in ("population", "experiments", "arms", "observations", "metrics_summary")
    )
    return {
        "status": "ok",
        "benchmark_data_dir": str(benchmark_dir),
        "benchmark_parquets_ready": parquets_ready,
        "sandbox_provider": os.getenv("SANDBOX_PROVIDER", "daytona"),
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
    evaluation = CausalEvaluationAgent().run(context)
    evaluation.update(causal_runtime_options())
    evaluation.update(recommendation_runtime_options())
    candidates = ExperimentGenerationSkill().run(context=context, evaluation=evaluation)
    return RecommendationAgent().run(candidates=candidates, evaluation=evaluation, context=context)


@app.post("/analyze/{experiment_id}")
def analyze(experiment_id: str, objective: str = "day7_retention") -> dict:
    """Post-experiment statistical analysis (programmatic + sandbox)."""
    context = RetrievalSkill().run(objective=objective, experiment_id=experiment_id)
    evaluation = CausalEvaluationAgent().run(context)
    validation_report = ValidationAgent(
        benchmark_dir=validation_runtime_options()["benchmark_dir"],
    ).run({**context, **validation_runtime_options()})
    return StatisticalAnalysisAgent().run(
        context=context,
        evaluation=evaluation,
        validation_report=validation_report,
    )


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
        "statistical_analysis": result.statistical_analysis,
    }
