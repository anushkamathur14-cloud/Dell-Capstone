#!/usr/bin/env python3
"""Export one decision packet JSON (any flag combo via env or args)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from src.runner.env import load_env

load_env()

from src.runner.pipeline import AgentFlags, execute_mode  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", default="exp_sanity_001_calibrated")
    parser.add_argument("--objective", default="day7_retention")
    parser.add_argument("--out", default="")
    parser.add_argument("--validation-llm", action="store_true")
    parser.add_argument("--causal-agent", action="store_true")
    parser.add_argument("--generation", action="store_true")
    parser.add_argument("--full", action="store_true", help="All agents on")
    args = parser.parse_args()

    if args.full:
        flags = AgentFlags(True, True, True)
    else:
        flags = AgentFlags(
            enable_validation_llm=args.validation_llm,
            enable_causal_agent_loop=args.causal_agent,
            enable_generation_agent=args.generation,
        )

    rec = execute_mode("export", flags, objective=args.objective, experiment_id=args.experiment_id)
    payload = {
        "flags": {
            "validation_llm": flags.enable_validation_llm,
            "causal_agent": flags.enable_causal_agent_loop,
            "generation": flags.enable_generation_agent,
        },
        "elapsed_seconds": rec.elapsed_seconds,
        "error": rec.error,
        "packet": rec.packet,
    }

    out = Path(args.out) if args.out else ROOT / "artifacts" / "decision_packets" / f"{args.experiment_id}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, default=str), encoding="utf-8")
    print(out)
    return 0 if not rec.error else 1


if __name__ == "__main__":
    raise SystemExit(main())
