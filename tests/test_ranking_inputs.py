"""Ranking envelope helpers (canonical v1; Slice A/C precursors)."""

from src.agent.ranking_inputs import ranking_candidates_from_context
from src.skills.retrieval import RetrievalSkill


def test_ranking_candidates_from_retrieval_stub() -> None:
    ctx = RetrievalSkill().run(objective="test", experiment_id="exp_fixture")
    cands = ranking_candidates_from_context(ctx)
    assert len(cands) >= 1
    assert cands[0]["candidate_name"] == ctx["metrics"][0].arm_id
    assert cands[0]["source"] == "retrieval_metrics"
