from src.agent.orchestrator import AdaptiveExperimentationOrchestrator


def test_orchestrator_smoke() -> None:
    orchestrator = AdaptiveExperimentationOrchestrator()
    result = orchestrator.run(objective="improve_retention", experiment_id="exp_001")
    assert result.recommendation["top_recommendation"] is not None
