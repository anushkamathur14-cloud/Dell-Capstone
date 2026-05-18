"""Workstream B (validation) and E (agent integration) contract tests.

Validates Pydantic schemas, non-empty/non-zero outputs, and LangGraph wiring.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from src.agent.orchestrator import AdaptiveExperimentationOrchestrator
from src.agent.recommendation_agent import RecommendationAgent, build_recommendation_graph
from src.agent.validation_agent import ValidationAgent, build_validation_graph
from src.data.models import (
    RecommendationReport,
    ValidationReport,
)
from src.skills.causal_evaluation import CausalEvaluationSkill
from src.skills.experiment_generation import ExperimentGenerationSkill
from src.skills.retrieval import RetrievalSkill
from src.skills.validation import ValidationSkill


# --- Workstream B: validation schema & outputs ---


def test_validation_report_schema_round_trip() -> None:
    context = RetrievalSkill().run(objective="day7_retention", experiment_id="exp_schema_b")
    payload = ValidationAgent().run(context)
    report = ValidationReport.model_validate(payload)
    assert report.schema_version == "v1.0"
    assert report.decision in {"go", "caution", "stop"}
    assert len(report.checks) > 0
    assert len(report.diagnostics_summary) > 0


def test_validation_checks_non_empty_and_have_names() -> None:
    context = RetrievalSkill().run(objective="day7_retention", experiment_id="exp_001")
    report = ValidationReport.model_validate(ValidationSkill().run(context))

    assert len(report.checks) >= 1
    for check in report.checks:
        assert check.name
        assert check.message
        assert check.severity in {"error", "warning", "info"}


def test_validation_go_path_has_zero_blocking_issues() -> None:
    from src.data.models import ArmVariant, Experiment, MetricsSummary

    payload = ValidationAgent().run(
        {
            "experiment": Experiment(
                experiment_id="exp_go",
                objective="day7_retention",
                status="active",
                traffic_split={"control": 0.5, "variant_a": 0.5},
                owner="test",
            ),
            "arms": [
                ArmVariant(
                    experiment_id="exp_go",
                    arm_id="control",
                    treatment_description="baseline",
                    treatment_type="baseline",
                ),
                ArmVariant(
                    experiment_id="exp_go",
                    arm_id="variant_a",
                    treatment_description="variant",
                    treatment_type="configured_bundle",
                ),
            ],
            "metrics": [
                MetricsSummary(
                    experiment_id="exp_go",
                    arm_id="control",
                    sample_size=1200,
                    retention=0.40,
                    variance=0.02,
                ),
                MetricsSummary(
                    experiment_id="exp_go",
                    arm_id="variant_a",
                    sample_size=1200,
                    retention=0.48,
                    variance=0.02,
                ),
            ],
        }
    )
    report = ValidationReport.model_validate(payload)
    assert report.decision == "go"
    assert report.issues == []


def test_validation_report_rejects_invalid_decision() -> None:
    with pytest.raises(ValidationError):
        ValidationReport.model_validate(
            {
                "schema_version": "v1.0",
                "decision": "invalid",
                "checks": [],
            }
        )


# --- Workstream E: agent graphs & orchestrator integration ---


def test_validation_langgraph_compiles_and_has_edges() -> None:
    graph = build_validation_graph()
    g = graph.get_graph()
    assert g.nodes
    assert len(g.edges) >= 5


def test_recommendation_langgraph_compiles_and_has_edges() -> None:
    graph = build_recommendation_graph()
    g = graph.get_graph()
    assert g.nodes
    assert len(g.edges) >= 3


def test_orchestrator_schema_version_and_non_empty_outputs() -> None:
    result = AdaptiveExperimentationOrchestrator().run(
        objective="improve_retention",
        experiment_id="exp_001",
    )

    assert result.schema_version == "v1.0"

    validation = ValidationReport.model_validate(result.validation_report)
    assert validation.decision in {"go", "caution"}
    assert len(validation.checks) > 0
    assert len(validation.diagnostics_summary) > 0

    recommendation = RecommendationReport.model_validate(result.recommendation)
    assert recommendation.ranking_method == "lift_aware_v1"
    assert recommendation.top_recommendation is not None
    assert len(recommendation.ranked_candidates) >= 1
    assert len(recommendation.explanation) > 0

    top = recommendation.top_recommendation
    assert top is not None
    assert top["score"] > 0
    assert top["rank"] == 1
    assert top.get("score_components", {}).get("retention", 0) > 0


def test_orchestrator_recommendation_scores_are_distinct_when_candidates_differ() -> None:
    result = AdaptiveExperimentationOrchestrator().run(
        objective="improve_retention",
        experiment_id="exp_001",
    )
    ranked = result.recommendation["ranked_candidates"]
    assert len(ranked) >= 2
    scores = [row["score"] for row in ranked]
    assert len(set(scores)) >= 2, "Expected distinct scores across candidates"
    assert max(scores) > min(scores)


def test_end_to_end_skill_chain_produces_evaluation_non_zero_lift() -> None:
    context = RetrievalSkill().run(objective="day7_retention", experiment_id="exp_001")
    evaluation = CausalEvaluationSkill().run(context)
    assert "uncertainty" in evaluation
    assert evaluation["uncertainty"] > 0
    lift = evaluation.get("estimated_lift") or evaluation.get("placeholder_lift")
    assert lift is not None

    candidates = ExperimentGenerationSkill().run(context=context, evaluation=evaluation)
    assert len(candidates) >= 2

    report = RecommendationReport.model_validate(
        RecommendationAgent().run(candidates=candidates, evaluation=evaluation, context=context)
    )
    assert report.top_recommendation is not None
    assert report.top_recommendation["score"] > 0
