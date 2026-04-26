"""Optional LLM helper scaffolds for world-building tasks.

Core simulation does not depend on this module.
"""

from __future__ import annotations


def generate_world_spec_prompt(natural_language_constraints: str) -> str:
    return (
        "Convert the following constraints into structured world spec fields for segments, "
        "treatment parameters, KPI definitions, and constraints. Keep output deterministic JSON.\n\n"
        f"Constraints:\n{natural_language_constraints}"
    )


def generate_scenario_prompt(world_summary: str) -> str:
    return (
        "Propose 3 scenario templates for adaptive experimentation benchmark runs with explicit hypotheses.\n\n"
        f"World summary:\n{world_summary}"
    )


def generate_experiment_summary_prompt(metrics_snapshot: str) -> str:
    return (
        "Write an analyst-style concise summary of experiment outcomes, tradeoffs, and next-best candidates.\n\n"
        f"Metrics:\n{metrics_snapshot}"
    )
