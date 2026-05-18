from src.agent.orchestrator import AdaptiveExperimentationOrchestrator


def test_orchestrator_smoke() -> None:
    orchestrator = AdaptiveExperimentationOrchestrator()
    result = orchestrator.run(objective="improve_retention", experiment_id="exp_001")
    assert result.schema_version == "v1.0"
    assert result.validation_report["decision"] in {"go", "caution"}
    assert result.recommendation["top_recommendation"] is not None
