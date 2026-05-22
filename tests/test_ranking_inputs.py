"""Ranking envelope helpers (canonical v1; Slice A/C precursors)."""

from src.agent.ranking_inputs import ranking_candidates_from_context
from src.skills.retrieval import RetrievalSkill


def test_ranking_candidates_from_benchmark_retrieval() -> None:
    ctx = RetrievalSkill().run(
        objective="day7_retention",
        experiment_id="exp_sanity_001_calibrated",
    )
    cands = ranking_candidates_from_context(ctx)
    assert len(cands) >= 4
    assert cands[0]["source"] == "retrieval_metrics"
    assert ctx.get("source") == "benchmark_parquet"
