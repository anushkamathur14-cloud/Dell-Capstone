"""Coordinator agent: entry point and LangSmith umbrella runs.

This module does **not** duplicate pipeline logic. It groups traces and exposes:
- **Canonical full pipeline** — delegates to ``AdaptiveExperimentationOrchestrator.run`` (four skills: retrieval → validation → causal evaluation → recommendation).
- **Smoke / minimal trace flow** — onboarding-only shortcut (retrieval → validation → ranking
  with fixed dummy eval/candidates); skips causal evaluation and experiment generation by design.
"""

from __future__ import annotations

from typing import Any

from src.agent.orchestrator import AdaptiveExperimentationOrchestrator, OrchestrationResult
from src.agent.traced_steps import trace_named
from src.observability.langsmith_trace import TraceNames


class CoordinatorAgent:
    """Outward-facing coordinator: umbrella LangSmith spans plus optional smoke flow.

    - ``run_full_pipeline``: same contract as the orchestrator (see ``OrchestrationResult``).
    - ``run_minimal_demo_flow``: **not** the canonical product path; use only for quick smokes.
    """

    def __init__(self) -> None:
        self._orchestrator = AdaptiveExperimentationOrchestrator()
        self.retrieval = self._orchestrator.retrieval
        self.validation = self._orchestrator.validation
        self.recommender = self._orchestrator.recommender

    @trace_named(TraceNames.COORDINATOR_RUN)
    def run_full_pipeline(self, objective: str, experiment_id: str) -> OrchestrationResult:
        """Delegate to the orchestrator: canonical four-skill synchronous pipeline (v1)."""
        return self._orchestrator.run(objective=objective, experiment_id=experiment_id)

    @trace_named(TraceNames.COORDINATOR_MINIMAL_DEMO)
    def run_minimal_demo_flow(self, objective: str, experiment_id: str) -> dict[str, Any]:
        """Smoke only: retrieval → validation → recommendation with stub eval/candidates."""

        from src.agent.traced_steps import run_recommendation_skill, run_retrieval_skill, run_validation_skill

        context = run_retrieval_skill(self.retrieval, objective=objective, experiment_id=experiment_id)
        validation_report = run_validation_skill(self.validation, context)

        if validation_report["decision"] == "stop":
            return {"status": "halted", "validation_report": validation_report}

        dummy_eval = {"uncertainty": 0.2, "ranked_directions": ["quick_demo"]}
        dummy_candidates = [
            {
                "candidate_name": f"{experiment_id}-demo-rank-a",
                "rationale": "Minimal demo candidate",
                "expected_tradeoff": "n/a",
                "target_segment": "all",
                "implementation_notes": "stub",
                "signal_from_eval": dummy_eval["ranked_directions"][0],
            }
        ]

        recommendation = run_recommendation_skill(
            self.recommender, candidates=dummy_candidates, evaluation=dummy_eval
        )
        return {
            "status": "ok",
            "flow": "smoke_minimal",
            "experiment_id": experiment_id,
            "objective": objective,
            "validation_report": validation_report,
            "recommendation": recommendation,
        }
