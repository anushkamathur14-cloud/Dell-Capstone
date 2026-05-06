"""Traced boundaries for skills (LangSmith-visible run units).

Each function maps 1:1 to a logical skill invocation. If `langsmith` is missing or
import fails, decorators become no-ops so local tests run without tracing.
"""

from __future__ import annotations

from typing import Any, Callable, TypeVar

from src.observability.langsmith_trace import TraceNames

F = TypeVar("F", bound=Callable[..., Any])


def trace_named(run_name: str) -> Callable[[F], F]:
    """Expose the same decorator for coordinator-level runs."""
    return _maybe_traceable(run_name)


def _maybe_traceable(run_name: str) -> Callable[[F], F]:
    try:
        from langsmith import traceable

        return traceable(name=run_name, run_type="chain")
    except Exception:

        def _noop_decorator(fn: F) -> F:
            return fn

        return _noop_decorator


@_maybe_traceable(TraceNames.RETRIEVAL_SKILL)
def run_retrieval_skill(skill: Any, *, objective: str, experiment_id: str) -> dict:
    return skill.run(objective=objective, experiment_id=experiment_id)


@_maybe_traceable(TraceNames.VALIDATION_SKILL)
def run_validation_skill(skill: Any, context: dict) -> dict:
    return skill.run(context)


@_maybe_traceable(TraceNames.CAUSAL_EVALUATION_SKILL)
def run_causal_evaluation_skill(skill: Any, context: dict) -> dict:
    return skill.run(context)


@_maybe_traceable(TraceNames.EXPERIMENT_GENERATION_SKILL)
def run_experiment_generation_skill(skill: Any, *, context: dict, evaluation: dict) -> list[dict]:
    return skill.run(context=context, evaluation=evaluation)


@_maybe_traceable(TraceNames.RECOMMENDATION_AGENT_V1)
def run_recommendation_skill(skill: Any, *, candidates: list[dict], evaluation: dict) -> dict:
    return skill.run(candidates=candidates, evaluation=evaluation)
