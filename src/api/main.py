"""FastAPI app stub."""

import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.agent.orchestrator import AdaptiveExperimentationOrchestrator
from src.agent.validation_agent import ValidationAgent
from src.api.benchmark_catalog import router as catalog_router
from src.api.orchestrate_history import init_db
from src.skills.retrieval import RetrievalSkill


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Adaptive Experimentation Agent", version="0.1.0", lifespan=lifespan)
app.include_router(catalog_router)

# CORS: default regex allows all Lovable preview + published hosts (see docs/DEPLOYMENT.md).
# CORS_FORCE_LOVABLE_REGEX=true (default) ignores a narrow CORS_ALLOW_ORIGINS on Railway.
_LOVABLE_ORIGIN_REGEX = (
    r"^https://([a-z0-9-]+\.)*lovable(project)?\.(app|dev)$"
    r"|^http://localhost(:\d+)?$"
    r"|^http://127\.0\.0\.1(:\d+)?$"
)
# adaptivegaming Lovable project 4d5eac12-ab80-4245-8c16-10dcccd1e662 (explicit-list fallback)
_ADAPTIVEGAMING_ORIGINS = frozenset(
    {
        "https://adaptivegaming.lovable.app",
        "https://preview--4d5eac12-ab80-4245-8c16-10dcccd1e662.lovable.app",
        "https://4d5eac12-ab80-4245-8c16-10dcccd1e662.lovableproject.com",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    }
)

_cors = os.getenv("CORS_ALLOW_ORIGINS", "").strip()
_force_regex = os.getenv("CORS_FORCE_LOVABLE_REGEX", "true").lower() in {"1", "true", "yes"}

if _force_regex or _cors in ("", "*"):
    app.add_middleware(
        CORSMiddleware,
        allow_origin_regex=_LOVABLE_ORIGIN_REGEX,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
else:
    origins = {o.strip() for o in _cors.split(",") if o.strip()} | _ADAPTIVEGAMING_ORIGINS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=sorted(origins),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/")
def root() -> dict:
    return {"service": "adaptive-experimentation-agent", "mode": "mvp-starter"}


@app.get("/health")
def health() -> dict:
    from src.api.orchestrate_history import db_path

    bdir = Path(_validation_runtime_options()["benchmark_dir"])
    return {
        "status": "ok",
        "benchmark_data_dir": str(bdir),
        "benchmark_parquets_ready": (bdir / "experiments.parquet").exists(),
        "run_history_db": str(db_path()),
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
    from src.api.orchestrate_history import record_orchestrate_failure, record_orchestrate_success

    try:
        orchestrator = AdaptiveExperimentationOrchestrator()
        result = orchestrator.run(objective=objective, experiment_id=experiment_id)
        payload = {
            "schema_version": result.schema_version,
            "experiment": result.experiment.model_dump(),
            "memory": result.memory.model_dump(),
            "metrics": [metric.model_dump() for metric in result.metrics],
            "validation_report": result.validation_report,
            "evaluation": result.evaluation,
            "candidates": result.candidates,
            "recommendation": result.recommendation,
        }
        rid = record_orchestrate_success(
            experiment_id=experiment_id,
            objective=objective,
            response=payload,
        )
        payload["run_record_id"] = rid
        return payload
    except Exception as exc:  # noqa: BLE001 — demo: persist failure then surface error
        rid = record_orchestrate_failure(
            experiment_id=experiment_id,
            objective=objective,
            error=str(exc),
        )
        raise HTTPException(
            status_code=500,
            detail={"message": str(exc), "run_record_id": rid},
        ) from exc
