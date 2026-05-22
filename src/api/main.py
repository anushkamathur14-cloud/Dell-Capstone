"""FastAPI app stub."""

import os

from fastapi import FastAPI

from src.agent.orchestrator import AdaptiveExperimentationOrchestrator
from src.agent.validation_agent import DEFAULT_BENCHMARK_DIR, ValidationAgent
from src.skills.retrieval import RetrievalSkill

app = FastAPI(title="Adaptive Experimentation Agent", version="0.1.0")


@app.get("/")
def root() -> dict:
    return {"service": "adaptive-experimentation-agent", "mode": "mvp-starter"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


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
def orchestrate(experiment_id: str, objective: str) -> dict:
    orchestrator = AdaptiveExperimentationOrchestrator()
    result = orchestrator.run(objective=objective, experiment_id=experiment_id)
    return {
        "experiment": result.experiment.model_dump(),
        "memory": result.memory.model_dump(),
        "metrics": [metric.model_dump() for metric in result.metrics],
        "validation_report": result.validation_report,
        "evaluation": result.evaluation,
        "candidates": result.candidates,
        "recommendation": result.recommendation,
    }
