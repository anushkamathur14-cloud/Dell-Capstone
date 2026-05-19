"""Experiment generation skill: schema-validated candidates from evaluation signals."""

from __future__ import annotations

from src.data.models import RecommendationCandidate
from src.generation.candidate_builder import build_candidates_from_context


class ExperimentGenerationSkill:
    def run(self, context: dict, evaluation: dict) -> list[RecommendationCandidate]:
        return build_candidates_from_context(context=context, evaluation=evaluation)
