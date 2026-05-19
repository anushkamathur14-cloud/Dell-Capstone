"""Shared runtime configuration for orchestrator and API routes."""

from __future__ import annotations

import os
from pathlib import Path

from src.agent.validation_agent import DEFAULT_BENCHMARK_DIR


def validation_runtime_options() -> dict:
    benchmark_dir = os.getenv("BENCHMARK_DATA_DIR", str(DEFAULT_BENCHMARK_DIR))
    enable_llm = os.getenv("ENABLE_VALIDATION_LLM", "false").lower() in {"1", "true", "yes"}
    return {"benchmark_dir": benchmark_dir, "enable_llm": enable_llm}


def recommendation_runtime_options() -> dict:
    enable_llm = os.getenv("ENABLE_RECOMMENDATION_LLM", "false").lower() in {"1", "true", "yes"}
    enable_llm_loop = os.getenv("ENABLE_RECOMMENDATION_LLM_LOOP", "false").lower() in {"1", "true", "yes"}
    return {
        "enable_llm": enable_llm,
        "enable_llm_loop": enable_llm_loop,
        "variance_lambda": float(os.getenv("RECOMMENDATION_VARIANCE_LAMBDA", "0.2")),
        "uncertainty_weight": float(os.getenv("RECOMMENDATION_UNCERTAINTY_WEIGHT", "0.2")),
    }


def causal_runtime_options() -> dict:
    enable_sandbox = os.getenv("ENABLE_CAUSAL_SANDBOX", "true").lower() in {"1", "true", "yes"}
    return {"enable_sandbox": enable_sandbox}


def retrieval_benchmark_dir() -> Path:
    return Path(os.getenv("BENCHMARK_DATA_DIR", str(DEFAULT_BENCHMARK_DIR)))
