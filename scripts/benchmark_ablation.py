#!/usr/bin/env python3
"""Methodology ablation: same experiment, multiple agent configurations.

  python scripts/benchmark_ablation.py
  python scripts/benchmark_ablation.py --modes full_agentic,causal_agent_sandbox

Writes: artifacts/benchmark_runs/<timestamp>/
  - summary.json, summary.md, modes/<mode>/decision_packet.json
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from src.runner.env import load_env  # noqa: E402

load_env()

from src.llm.azure_factory import is_azure_configured  # noqa: E402
from src.runner.pipeline import AgentFlags, RunRecord, execute_mode  # noqa: E402

MODES: dict[str, AgentFlags] = {
    "stub_canonical": AgentFlags(),
    "validation_llm": AgentFlags(enable_validation_llm=True),
    "causal_programmatic": AgentFlags(),
    "causal_agent": AgentFlags(enable_causal_agent_loop=True),
    "causal_agent_sandbox": AgentFlags(
        enable_causal_agent_loop=True, causal_require_sandbox=True
    ),
    "generation_only": AgentFlags(enable_generation_agent=True),
    "hybrid_dell_demo": AgentFlags(
        enable_validation_llm=True, enable_generation_agent=True
    ),
    "full_agentic": AgentFlags(
        enable_validation_llm=True,
        enable_causal_agent_loop=True,
        enable_generation_agent=True,
    ),
}


def _md_table(records: list[RunRecord]) -> str:
    lines = [
        "# Ablation summary",
        "",
        "| mode | sec | validation | eval source | top candidate | top source | error |",
        "|------|-----|------------|-------------|---------------|------------|-------|",
    ]
    for r in records:
        p = r.packet
        v = p.get("validation", {}) if p else {}
        e = p.get("evaluation", {}) if p else {}
        rec = p.get("recommendation", {}) if p else {}
        lines.append(
            f"| {r.mode} | {r.elapsed_seconds} | {v.get('decision','-')} "
            f"| {e.get('source','-')} | {rec.get('top_name','-')} "
            f"| {rec.get('top_source','-')} | {r.error or ''} |"
        )
    lines.append("")
    lines.append("Negative or null results are expected for some modes — compare deltas in the call.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--experiment-id", default=os.getenv("E2E_EXPERIMENT_ID", "exp_sanity_001_calibrated"))
    parser.add_argument("--objective", default=os.getenv("E2E_OBJECTIVE", "day7_retention"))
    parser.add_argument("--modes", default=",".join(MODES.keys()), help="Comma-separated mode names")
    parser.add_argument("--langsmith", action="store_true", help="Set LANGSMITH_TRACING=true for all runs")
    args = parser.parse_args()

    if not is_azure_configured():
        print("ERROR: AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY required in .env")
        return 1

    if args.langsmith:
        os.environ["LANGSMITH_TRACING"] = "true"
        os.environ["LANGCHAIN_TRACING_V2"] = "true"
        print("LangSmith tracing ON — check LANGSMITH_API_KEY and project:", os.getenv("LANGSMITH_PROJECT"))

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_dir = ROOT / "artifacts" / "benchmark_runs" / stamp
    out_dir.mkdir(parents=True, exist_ok=True)

    selected = [m.strip() for m in args.modes.split(",") if m.strip()]
    records: list[RunRecord] = []

    for mode in selected:
        if mode not in MODES:
            print(f"Unknown mode: {mode}")
            return 1
        print(f"\n--- {mode} ---")
        rec = execute_mode(
            mode,
            MODES[mode],
            objective=args.objective,
            experiment_id=args.experiment_id,
        )
        records.append(rec)
        mode_dir = out_dir / "modes" / mode
        mode_dir.mkdir(parents=True, exist_ok=True)
        (mode_dir / "decision_packet.json").write_text(
            json.dumps(
                {
                    "mode": rec.mode,
                    "flags": asdict(rec.flags),
                    "elapsed_seconds": rec.elapsed_seconds,
                    "error": rec.error,
                    "packet": rec.packet,
                },
                indent=2,
                default=str,
            ),
            encoding="utf-8",
        )
        print(json.dumps(rec.packet.get("recommendation", {}), indent=2, default=str) if rec.packet else rec.error)

    summary = {
        "timestamp": stamp,
        "experiment_id": args.experiment_id,
        "objective": args.objective,
        "langsmith_tracing": os.getenv("LANGSMITH_TRACING"),
        "runs": [
            {
                "mode": r.mode,
                "flags": asdict(r.flags),
                "elapsed_seconds": r.elapsed_seconds,
                "error": r.error,
                "packet": r.packet,
            }
            for r in records
        ],
    }
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    (out_dir / "summary.md").write_text(_md_table(records), encoding="utf-8")

    print(f"\nWrote {out_dir}")
    print("Open summary.md for Dell call table.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
