"""Tests for skill registry, causal agent, statistical analysis, recommendation loop."""

from __future__ import annotations

from src.agent.causal_evaluation_agent import CausalEvaluationAgent, build_causal_evaluation_graph
from src.agent.recommendation_agent import build_recommendation_graph
from src.agent.statistical_analysis_agent import StatisticalAnalysisAgent
from src.agent.tools.registry import SkillRegistry
from src.data.models import StatisticalAnalysisReport
from src.skills.retrieval import RetrievalSkill


def test_skill_registry_invoke_retrieval() -> None:
    registry = SkillRegistry()
    context = registry.invoke("retrieval_skill", objective="day7_retention", experiment_id="exp_001")
    assert "experiment" in context
    assert "metrics" in context


def test_causal_agent_graph_and_programmatic() -> None:
    graph = build_causal_evaluation_graph()
    assert {"programmatic", "design", "sandbox"}.issubset(set(graph.get_graph().nodes))

    context = RetrievalSkill().run(objective="day7_retention", experiment_id="exp_001")
    evaluation = CausalEvaluationAgent().run(context)
    assert evaluation.get("_stub") is False
    assert evaluation.get("estimator") == "difference_in_means_v1"
    assert "experiment_design" in evaluation


def test_statistical_analysis_after_experiment() -> None:
    context = RetrievalSkill().run(objective="day7_retention", experiment_id="exp_001")
    report = StatisticalAnalysisAgent().run(context=context, evaluation={}, validation_report={})
    parsed = StatisticalAnalysisReport.model_validate(report)
    assert parsed.experiment_id == context["experiment"].experiment_id
    assert parsed.programmatic_summary
    assert parsed.programmatic_results.get("estimated_lift") is not None


def test_recommendation_graph_includes_llm_tool_loop() -> None:
    graph = build_recommendation_graph()
    assert "llm_tool_loop" in set(graph.get_graph().nodes)
