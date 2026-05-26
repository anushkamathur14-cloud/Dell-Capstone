"""FastAPI app stub."""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.agent.orchestrator import AdaptiveExperimentationOrchestrator
from src.agent.validation_agent import ValidationAgent
from src.skills.retrieval import RetrievalSkill

app = FastAPI(title="Adaptive Experimentation Agent", version="0.1.0")

# CORS: explicit comma-separated origins in CORS_ALLOW_ORIGINS, or default Lovable hosts
# (avoids needing Railway Variables for first deploy).
_cors = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
if _cors in ("", "*"):
    _lovable_re = (
        r"^https://[\w.-]+\.lovable\.app$"
        r"|^https://[\w.-]+\.lovableproject\.com$"
        r"|^https://[\w.-]+\.lovable\.dev$"
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=_lovable_re,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in _cors.split(",") if o.strip()],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


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
        "schema_version": result.schema_version,
        "experiment": result.experiment.model_dump(),
        "memory": result.memory.model_dump(),
        "metrics": [metric.model_dump() for metric in result.metrics],
        "validation_report": result.validation_report,
        "evaluation": result.evaluation,
        "candidates": result.candidates,
        "recommendation": result.recommendation,
    }
