"""Run canonical pipeline with explicit agent flags and exportable packets."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

from src.agent.coordinator import CoordinatorAgent
from src.agent.orchestrator import OrchestrationResult


@dataclass
class AgentFlags:
    enable_validation_llm: bool = False
    enable_causal_agent_loop: bool = False
    enable_generation_agent: bool = False
    causal_require_sandbox: bool = False


@dataclass
class RunRecord:
    mode: str
    flags: AgentFlags
    elapsed_seconds: float
    experiment_id: str
    objective: str
    packet: dict[str, Any]
    error: str | None = None


def result_to_packet(result: OrchestrationResult) -> dict[str, Any]:
    top = result.recommendation.get("top_recommendation")
    return {
        "schema_version": result.schema_version,
        "experiment_id": result.experiment.experiment_id,
        "objective": result.experiment.objective,
        "retrieval_metrics_count": len(result.metrics),
        "arm_ids": [m.arm_id for m in result.metrics],
        "validation": {
            "decision": result.validation_report.get("decision"),
            "benchmark_loaded": result.validation_report.get("benchmark_loaded"),
            "diagnostics_source": result.validation_report.get("diagnostics_source"),
            "issues_count": len(result.validation_report.get("issues") or []),
            "warnings_count": len(result.validation_report.get("warnings") or []),
            "diagnostics_preview": (result.validation_report.get("diagnostics_summary") or "")[:400],
        },
        "evaluation": {
            "source": result.evaluation.get("source"),
            "schema_version": result.evaluation.get("schema_version"),
            "estimated_lift": result.evaluation.get("estimated_lift"),
            "uncertainty": result.evaluation.get("uncertainty"),
            "ranked_directions": result.evaluation.get("ranked_directions"),
            "segment_effects": result.evaluation.get("segment_effects"),
            "analysis_notes": result.evaluation.get("analysis_notes"),
        },
        "candidates": {
            "count": len(result.candidates),
            "sources": sorted({c.get("source", "?") for c in result.candidates}),
            "names": [c.get("candidate_name") for c in result.candidates],
        },
        "recommendation": {
            "top_name": top.get("candidate_name") if top else None,
            "top_source": top.get("source") if top else None,
            "top_score": top.get("score") if top else None,
            "top_rationale_preview": (top.get("rationale") or "")[:300] if top else None,
        },
    }


def run_pipeline(
    *,
    objective: str,
    experiment_id: str,
    flags: AgentFlags,
    use_coordinator: bool = True,
) -> OrchestrationResult:
    import os

    os.environ["ENABLE_VALIDATION_LLM"] = "true" if flags.enable_validation_llm else "false"
    os.environ["ENABLE_CAUSAL_AGENT_LOOP"] = "true" if flags.enable_causal_agent_loop else "false"
    os.environ["ENABLE_GENERATION_AGENT"] = "true" if flags.enable_generation_agent else "false"
    os.environ["CAUSAL_REQUIRE_SANDBOX"] = "true" if flags.causal_require_sandbox else "false"

    if use_coordinator:
        return CoordinatorAgent().run_full_pipeline(objective=objective, experiment_id=experiment_id)
    from src.agent.orchestrator import AdaptiveExperimentationOrchestrator

    return AdaptiveExperimentationOrchestrator().run(objective=objective, experiment_id=experiment_id)


def execute_mode(
    mode: str,
    flags: AgentFlags,
    *,
    objective: str,
    experiment_id: str,
) -> RunRecord:
    start = time.perf_counter()
    try:
        result = run_pipeline(objective=objective, experiment_id=experiment_id, flags=flags)
        packet = result_to_packet(result)
        err = None
    except Exception as exc:
        packet = {}
        err = f"{type(exc).__name__}: {exc}"
    elapsed = time.perf_counter() - start
    return RunRecord(
        mode=mode,
        flags=flags,
        elapsed_seconds=round(elapsed, 2),
        experiment_id=experiment_id,
        objective=objective,
        packet=packet,
        error=err,
    )
