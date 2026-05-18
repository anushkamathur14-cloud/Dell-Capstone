"""Input validation before recommendation scoring."""

from __future__ import annotations

from typing import Any


def run_input_checks(
    candidates: list[Any],
    evaluation: dict[str, Any],
) -> list[str]:
    warnings: list[str] = []

    if not candidates:
        warnings.append("No candidates supplied; recommendation will be empty.")

    if len(candidates) == 1:
        warnings.append("Only one candidate supplied; ranking is degenerate.")

    if "uncertainty" not in evaluation:
        warnings.append("Evaluation missing 'uncertainty'; using default 0.1 in scoring.")

    for candidate in candidates:
        metric_stub = (
            candidate.metric_stub
            if hasattr(candidate, "metric_stub")
            else (candidate.get("metric_stub") if isinstance(candidate, dict) else None)
        )
        if not metric_stub or metric_stub.get("retention") is None:
            name = getattr(candidate, "candidate_name", None) or candidate.get("candidate_name", "unknown")
            warnings.append(f"Candidate '{name}' has no retention in metric_stub; score may be flat.")

    return warnings
