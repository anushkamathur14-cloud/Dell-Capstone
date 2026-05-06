from src.agent.coordinator import CoordinatorAgent


def test_minimal_demo_flow_ok() -> None:
    coord = CoordinatorAgent()
    out = coord.run_minimal_demo_flow(objective="improve_retention", experiment_id="exp_test_min")
    assert out["status"] == "ok"
    assert out["flow"] == "smoke_minimal"
    assert out["recommendation"]["top_recommendation"] is not None


def test_full_pipeline_via_coordinator() -> None:
    coord = CoordinatorAgent()
    result = coord.run_full_pipeline(objective="improve_retention", experiment_id="exp_test_full")
    assert result.validation_report["decision"] != "stop"
    assert result.candidates
    assert result.recommendation["top_recommendation"] is not None
