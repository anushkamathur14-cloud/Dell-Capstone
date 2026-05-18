from src.agent.validation_agent import ValidationAgent, build_validation_graph
from src.data.models import ArmVariant, Experiment, MetricsSummary
from src.skills.retrieval import RetrievalSkill
from src.skills.validation import ValidationSkill


def test_validation_graph_has_expected_nodes() -> None:
    graph = build_validation_graph()
    node_names = set(graph.get_graph().nodes)
    assert {"structural", "metrics", "decide"}.issubset(node_names)


def test_validation_agent_emits_stop_on_critical_context() -> None:
    agent = ValidationAgent()
    report = agent.run(
        {
            "experiment": Experiment(
                experiment_id="exp_bad",
                objective="day7_retention",
                status="active",
                traffic_split={},
                owner="test",
            ),
            "arms": [],
            "metrics": [],
        }
    )
    assert report["decision"] == "stop"
    assert len(report["issues"]) >= 2
    assert report["schema_version"] == "v1.0"
    assert any(check["name"] == "metrics_present" for check in report["checks"])


def test_validation_skill_delegates_to_agent() -> None:
    context = RetrievalSkill().run(objective="day7_retention", experiment_id="exp_001")
    report = ValidationSkill().run(context)
    assert report["decision"] in {"go", "caution", "stop"}
    assert "checks" in report


def test_multi_arm_metrics_can_reach_go() -> None:
    agent = ValidationAgent()
    report = agent.run(
        {
            "experiment": Experiment(
                experiment_id="exp_ok",
                objective="day7_retention",
                status="active",
                traffic_split={"control": 0.5, "variant_a": 0.5},
                owner="test",
            ),
            "arms": [
                ArmVariant(
                    experiment_id="exp_ok",
                    arm_id="control",
                    treatment_description="baseline",
                    treatment_type="baseline",
                ),
                ArmVariant(
                    experiment_id="exp_ok",
                    arm_id="variant_a",
                    treatment_description="variant",
                    treatment_type="configured_bundle",
                ),
            ],
            "metrics": [
                MetricsSummary(
                    experiment_id="exp_ok",
                    arm_id="control",
                    sample_size=1200,
                    retention=0.40,
                    variance=0.02,
                ),
                MetricsSummary(
                    experiment_id="exp_ok",
                    arm_id="variant_a",
                    sample_size=1200,
                    retention=0.48,
                    variance=0.02,
                ),
            ],
        }
    )
    assert report["decision"] == "go"
    assert report["issues"] == []
