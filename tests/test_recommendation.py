"""Unit tests for RecommendationSkill scoring."""

from __future__ import annotations

from typing import Optional

from src.skills.recommendation import RecommendationSkill


def _candidate(
    name: str,
    *,
    retention: Optional[float] = None,
    conversion: Optional[float] = None,
    risk: Optional[float] = None,
    complexity: Optional[float] = None,
) -> dict:
    metric_stub: dict = {}
    if retention is not None:
        metric_stub["retention"] = retention
    if conversion is not None:
        metric_stub["conversion"] = conversion
    out: dict = {"candidate_name": name, "metric_stub": metric_stub}
    if risk is not None:
        out["risk"] = risk
    if complexity is not None:
        out["complexity"] = complexity
    return out


def test_higher_retention_ranks_first() -> None:
    skill = RecommendationSkill()
    result = skill.run(
        candidates=[
            _candidate("low", retention=0.4, conversion=0.1),
            _candidate("high", retention=0.8, conversion=0.1),
        ],
        evaluation={"uncertainty": 0.1},
    )
    top = result["top_recommendation"]
    assert top is not None
    assert top["candidate_name"] == "high"
    assert top["score"] > result["ranked_candidates"][1]["score"]
    assert "score_components" in top
    assert "retention" in top["score_components"]


def test_lower_uncertainty_boosts_score() -> None:
    skill = RecommendationSkill()
    candidate = _candidate("arm", retention=0.5, conversion=0.5)
    low_unc = skill.run([candidate], evaluation={"uncertainty": 0.0})["top_recommendation"]
    high_unc = skill.run([candidate], evaluation={"uncertainty": 1.0})["top_recommendation"]
    assert low_unc is not None and high_unc is not None
    assert low_unc["score"] > high_unc["score"]
    assert low_unc["score_components"]["confidence"] > high_unc["score_components"]["confidence"]


def test_risk_and_complexity_reduce_score_when_present() -> None:
    skill = RecommendationSkill()
    base = skill.run(
        [_candidate("base", retention=0.6, conversion=0.6)],
        evaluation={"uncertainty": 0.2},
    )["top_recommendation"]
    penalized = skill.run(
        [_candidate("penalized", retention=0.6, conversion=0.6, risk=0.8, complexity=0.9)],
        evaluation={"uncertainty": 0.2},
    )["top_recommendation"]
    assert base is not None and penalized is not None
    assert base["score"] > penalized["score"]
    assert "risk_safety" in penalized["score_components"]
    assert "simplicity" in penalized["score_components"]


def test_empty_candidates_returns_none_top() -> None:
    result = RecommendationSkill().run([], evaluation={})
    assert result["top_recommendation"] is None
    assert result["ranked_candidates"] == []
