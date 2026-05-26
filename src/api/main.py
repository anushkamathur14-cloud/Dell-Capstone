"""FastAPI service for the adaptive experimentation agent."""

import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.agent.orchestrator import AdaptiveExperimentationOrchestrator
from src.agent.validation_agent import ValidationAgent
from src.skills.retrieval import RetrievalSkill

app = FastAPI(title="Adaptive Experimentation Agent", version="0.1.0")

_cors_origins = os.getenv("CORS_ALLOW_ORIGINS", "*")
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in _cors_origins.split(",") if origin.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _benchmark_dir() -> Path:
    from src.config.settings import get_settings

    return Path(get_settings().benchmark_data_dir)


@app.get("/")
def root() -> dict:
    return {"service": "adaptive-experimentation-agent", "mode": "mvp-starter"}


@app.get("/health")
def health() -> dict:
    benchmark_dir = _benchmark_dir()
    required = ("population", "experiments", "arms", "observations", "metrics_summary")
    parquets_ready = all((benchmark_dir / f"{name}.parquet").exists() for name in required)
    return {
        "status": "ok",
        "benchmark_data_dir": str(benchmark_dir),
        "benchmark_parquets_ready": parquets_ready,
    }


def _validation_runtime_options() -> dict:
    from src.config.settings import get_settings

    settings = get_settings()
    return {
        "benchmark_dir": settings.benchmark_data_dir,
        "enable_llm": settings.enable_validation_llm,
    }


@app.post("/validate/{experiment_id}")
def validate(experiment_id: str, objective: str = "day7_retention") -> dict:
    context = RetrievalSkill().run(objective=objective, experiment_id=experiment_id)
    context.update(_validation_runtime_options())
    return ValidationAgent(
        benchmark_dir=context["benchmark_dir"],
        enable_llm=context["enable_llm"],
    ).run(context)


@app.post("/orchestrate/{experiment_id}")
def orchestrate(experiment_id: str, objective: str = "improve_retention") -> dict:
    result = AdaptiveExperimentationOrchestrator().run(
        objective=objective,
        experiment_id=experiment_id,
    )
    return {
        "schema_version": result.schema_version,
        "experiment": result.experiment.model_dump(),
        "memory": result.memory.model_dump(),
        "metrics": [metric.model_dump() for metric in result.metrics],
        "validation_report": result.validation_report,
        "evaluation": result.evaluation,
        "candidates": result.candidates,
        "recommendation": result.recommendation,
    }
