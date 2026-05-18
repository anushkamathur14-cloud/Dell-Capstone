"""Sort scored candidates and assign ranks."""

from __future__ import annotations

from typing import Any


def rank_scored_candidates(scored: list[dict[str, Any]]) -> list[dict[str, Any]]:
    ranked = sorted(scored, key=lambda row: row["score"], reverse=True)
    for index, row in enumerate(ranked, start=1):
        row["rank"] = index
    return ranked
