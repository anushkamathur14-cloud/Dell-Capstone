"""Optional LangSmith trace wrapper around benchmark generation."""

from __future__ import annotations

from typing import Any

from src.observability.langsmith_trace import TraceNames


def _traceable(name: str):
    try:
        from langsmith import traceable

        return traceable(name=name, run_type="chain")
    except Exception:

        def _noop(fn):
            return fn

        return _noop


@_traceable(TraceNames.BENCHMARK_GENERATION)
def run_benchmark_generation_traced(**kwargs: Any) -> dict:
    """Same as ``synthetic_env.pipeline.run_generation``, visible as benchmark_generation."""

    from synthetic_env.pipeline import run_generation

    return run_generation(**kwargs)
