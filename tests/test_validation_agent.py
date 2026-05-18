from pathlib import Path

import pytest

from src.agent.validation_agent import ValidationAgent, build_validation_graph
from src.data.models import ArmVariant, Experiment, MetricsSummary
from src.skills.retrieval import RetrievalSkill
from src.skills.validation import ValidationSkill
from src.validation.llm_diagnostics import generate_diagnostics_summary


def test_validation_graph_has_expected_nodes() -> None:
    graph = build_validation_graph()
    node_names = set(graph.get_graph().nodes)
    assert {
        "structural",
        "metrics",
        "benchmark",
        "world_spec",
        "decide",
        "llm_diagnostics",
    }.issubset(node_names)


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
    assert report["diagnostics_summary"]
    assert report["diagnostics_source"] == "template"


def test_warnings_alone_do_not_stop_pipeline() -> None:
    agent = ValidationAgent()
    report = agent.run(
        {
            "experiment": Experiment(
                experiment_id="exp_warn",
                objective="day7_retention",
                status="active",
                traffic_split={"control": 0.6, "variant_a": 0.3},
                owner="test",
            ),
            "arms": [
                ArmVariant(
                    experiment_id="exp_warn",
                    arm_id="control",
                    treatment_description="baseline",
                    treatment_type="baseline",
                )
            ],
            "metrics": [
                MetricsSummary(
                    experiment_id="exp_warn",
                    arm_id="control",
                    sample_size=1200,
                    retention=0.40,
                    variance=0.02,
                )
            ],
        }
    )
    assert report["decision"] == "caution"
    assert report["issues"] == []
    assert report["warnings"]


def test_validation_skill_delegates_to_agent() -> None:
    context = RetrievalSkill().run(objective="day7_retention", experiment_id="exp_001")
    report = ValidationSkill().run(context)
    assert report["decision"] in {"go", "caution", "stop"}
    assert "checks" in report
    assert "diagnostics_summary" in report


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


def test_template_diagnostics_summary() -> None:
    summary, source = generate_diagnostics_summary(
        decision="caution",
        issues=[],
        warnings=["Traffic split should sum to 1.0."],
        checks=[
            {
                "name": "traffic_split_sum",
                "passed": False,
                "message": "Traffic split should sum to 1.0.",
                "severity": "warning",
                "details": {},
            }
        ],
        use_llm=False,
    )
    assert source == "template"
    assert "caution" in summary.lower()


@pytest.mark.slow
def test_benchmark_checks_when_parquets_exist(tmp_path: Path) -> None:
    from synthetic_env.pipeline import run_generation

    experiment_id = "exp_benchmark_test"
    run_generation(n_users=250, experiment_id=experiment_id, seed=7, output_dir=tmp_path)

    agent = ValidationAgent(benchmark_dir=tmp_path)
    report = agent.run(
        {
            "experiment": Experiment(
                experiment_id=experiment_id,
                objective="day7_retention",
                status="active",
                traffic_split={"control": 0.4, "fast_progression": 0.3, "guided_onboarding": 0.3},
                owner="test",
            ),
            "arms": [],
            "metrics": [],
        }
    )
    assert report["benchmark_loaded"] is True
    assert any(check["name"].startswith("benchmark_") for check in report["checks"])
