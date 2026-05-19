from src.data.models import Experiment, RecommendationCandidate
from src.skills.recommendation import RecommendationSkill
from src.skills.validation import ValidationSkill


def test_recommendation_ranking_responds_to_candidate_metrics() -> None:
    skill = RecommendationSkill()
    candidates = [
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

    result = skill.run(candidates=candidates, evaluation={"uncertainty": 0.1})
    assert result["ranked_candidates"][0]["candidate_name"] == "high-retention"
    assert result["ranked_candidates"][0]["score"] > result["ranked_candidates"][1]["score"]


def test_validation_can_emit_stop_decision() -> None:
    skill = ValidationSkill()
    context = {
        "experiment": Experiment(
            experiment_id="exp_001",
            objective="improve_retention",
            status="active",
            traffic_split={},
            owner="test",
        ),
        "metrics": [],
    }

    result = skill.run(context)
    assert result["decision"] == "stop"
    assert len(result["issues"]) == 2
