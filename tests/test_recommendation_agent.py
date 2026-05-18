from src.agent.recommendation_agent import RecommendationAgent, build_recommendation_graph
from src.data.models import RecommendationCandidate
from src.recommendation.llm_explanation import generate_recommendation_explanation
from src.recommendation.scoring import score_candidate
from src.skills.experiment_generation import ExperimentGenerationSkill
from src.skills.recommendation import RecommendationSkill
from src.skills.retrieval import RetrievalSkill
from src.skills.causal_evaluation import CausalEvaluationSkill


def _sample_candidates() -> list[RecommendationCandidate]:
    return [
        RecommendationCandidate(
            candidate_name="low-retention",
            parameter_changes={},
            rationale="lower baseline",
            expected_tradeoff="none",
            target_segment="all",
            implementation_notes="n/a",
            signal_from_eval="dir-a",
            metric_stub={"retention": 0.35, "variance": 0.06},
        ),
        RecommendationCandidate(
            candidate_name="high-retention",
            parameter_changes={},
            rationale="higher baseline",
            expected_tradeoff="none",
            target_segment="all",
            implementation_notes="n/a",
            signal_from_eval="dir-b",
            metric_stub={"retention": 0.55, "variance": 0.02},
        ),
    ]


def test_recommendation_graph_has_expected_nodes() -> None:
    graph = build_recommendation_graph()
    node_names = set(graph.get_graph().nodes)
    assert {"prepare", "score", "rank", "explain"}.issubset(node_names)


def test_score_candidate_uses_retention_and_variance() -> None:
    low = score_candidate(_sample_candidates()[0], {"uncertainty": 0.1})
    high = score_candidate(_sample_candidates()[1], {"uncertainty": 0.1})
    assert high["score"] > low["score"]
    assert "score_components" in high


def test_recommendation_agent_ranks_higher_retention_first() -> None:
    agent = RecommendationAgent()
    report = agent.run(candidates=_sample_candidates(), evaluation={"uncertainty": 0.1})
    assert report["top_recommendation"]["candidate_name"] == "high-retention"
    assert report["ranked_candidates"][0]["rank"] == 1
    assert report["explanation"]
    assert report["ranking_method"] == "lift_aware_v1"


def test_recommendation_skill_delegates_to_agent() -> None:
    evaluation = {"uncertainty": 0.1}
    report = RecommendationSkill().run(candidates=_sample_candidates(), evaluation=evaluation)
    assert report["top_recommendation"] is not None
    assert len(report["ranked_candidates"]) == 2


def test_pipeline_generation_produces_multiple_candidates() -> None:
    context = RetrievalSkill().run(objective="day7_retention", experiment_id="exp_001")
    evaluation = CausalEvaluationSkill().run(context)
    candidates = ExperimentGenerationSkill().run(context=context, evaluation=evaluation)
    assert len(candidates) >= 2


def test_template_explanation() -> None:
    top = score_candidate(_sample_candidates()[1], {"uncertainty": 0.1})
    ranked = [top]
    summary, source = generate_recommendation_explanation(
        top_recommendation=top,
        ranked_candidates=ranked,
        evaluation={"uncertainty": 0.1},
        warnings=[],
        use_llm=False,
    )
    assert source == "template"
    assert "high-retention" in summary
