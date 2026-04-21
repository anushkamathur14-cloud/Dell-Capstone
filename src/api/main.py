"""FastAPI app stub."""

from fastapi import FastAPI

from src.agent.orchestrator import AdaptiveExperimentationOrchestrator

app = FastAPI(title="Adaptive Experimentation Agent", version="0.1.0")


@app.get("/")
def root() -> dict:
    return {"service": "adaptive-experimentation-agent", "mode": "mvp-starter"}


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/orchestrate/{experiment_id}")
def orchestrate(experiment_id: str, objective: str) -> dict:
    orchestrator = AdaptiveExperimentationOrchestrator()
    result = orchestrator.run(objective=objective, experiment_id=experiment_id)
    return {
        "experiment": result.experiment.model_dump(),
        "memory": result.memory.model_dump(),
        "metrics": [metric.model_dump() for metric in result.metrics],
        "recommendation": result.recommendation,
    }
