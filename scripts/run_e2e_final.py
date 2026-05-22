#!/usr/bin/env python3
"""Full agentic E2E + decision packet + optional LangSmith trace."""

from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

from src.runner.env import load_env

load_env()

os.environ["ENABLE_VALIDATION_LLM"] = "true"
os.environ["ENABLE_CAUSAL_AGENT_LOOP"] = "true"
os.environ["ENABLE_GENERATION_AGENT"] = "true"

if os.getenv("ENABLE_LANGSMITH_TRACE", "false").lower() in {"1", "true", "yes"}:
    os.environ["LANGSMITH_TRACING"] = "true"
    os.environ["LANGCHAIN_TRACING_V2"] = "true"

from src.llm.azure_factory import is_azure_configured
from src.runner.pipeline import AgentFlags, execute_mode


def main() -> int:
    if not is_azure_configured():
        print("ERROR: Set AZURE_OPENAI_ENDPOINT and AZURE_OPENAI_API_KEY in .env")
        return 1

    experiment_id = os.getenv("E2E_EXPERIMENT_ID", "exp_sanity_001_calibrated")
    objective = os.getenv("E2E_OBJECTIVE", "day7_retention")

    print("=== Final agentic E2E ===")
    if os.getenv("LANGSMITH_TRACING") == "true":
        print("LangSmith tracing ON — project:", os.getenv("LANGSMITH_PROJECT"))

    rec = execute_mode(
        "full_agentic",
        AgentFlags(True, True, True),
        objective=objective,
        experiment_id=experiment_id,
    )

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = ROOT / "artifacts" / "decision_packets" / f"final_{stamp}.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(
        json.dumps(
            {"elapsed_seconds": rec.elapsed_seconds, "error": rec.error, "packet": rec.packet},
            indent=2,
            default=str,
        ),
        encoding="utf-8",
    )

    print(json.dumps(rec.packet, indent=2, default=str))
    print(f"\nDecision packet: {out}")
    if os.getenv("LANGSMITH_TRACING") == "true":
        print("View trace: langsmith trace list --project", os.getenv("LANGSMITH_PROJECT"))
    return 0 if not rec.error else 1


if __name__ == "__main__":
    raise SystemExit(main())
