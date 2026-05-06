#!/usr/bin/env python3
"""Minimal traced flow for LangSmith: retrieval → validation → recommendation (stub).

Usage (from repo root, venv activated):

    export LANGSMITH_TRACING=true
    export LANGSMITH_API_KEY=...
    export LANGSMITH_PROJECT=dell-capstone-adaptive-exp-agent

    PYTHONPATH=src:. python scripts/run_traced_dummy_flow.py

Optional: run traced synthetic benchmark generation first:

    PYTHONPATH=src:. python scripts/run_traced_dummy_flow.py --with-benchmark
"""

from __future__ import annotations

import argparse

from src.agent.coordinator import CoordinatorAgent


def main() -> None:
    parser = argparse.ArgumentParser(description="Run minimal LangSmith-traced coordinator demo.")
    parser.add_argument("--objective", default="improve day-7 retention", help="Optimization objective.")
    parser.add_argument("--experiment-id", default="exp_langsmith_demo_001")
    parser.add_argument(
        "--with-benchmark",
        action="store_true",
        help="Also run traced synthetic benchmark_generation (writes parquet artifacts).",
    )
    parser.add_argument("--benchmark-users", type=int, default=500)
    args = parser.parse_args()

    if args.with_benchmark:
        from synthetic_env.traced_pipeline import run_benchmark_generation_traced

        run_benchmark_generation_traced(
            n_users=args.benchmark_users,
            experiment_id="exp_benchmark_trace_smoke",
            seed=42,
            output_dir="synthetic_env/benchmarks/generated_langsmith_demo",
        )

    coord = CoordinatorAgent()
    out = coord.run_minimal_demo_flow(objective=args.objective, experiment_id=args.experiment_id)
    print(out)


if __name__ == "__main__":
    main()
