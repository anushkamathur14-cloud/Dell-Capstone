#!/usr/bin/env python3
"""Run canonical orchestration end-to-end (loads .env if present)."""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))

env_path = ROOT / ".env"
if env_path.exists():
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())


def main() -> int:
    from src.agent.orchestrator import AdaptiveExperimentationOrchestrator

    orchestrator = AdaptiveExperimentationOrchestrator()
    experiment_id = os.getenv("E2E_EXPERIMENT_ID", "exp_sanity_001_calibrated")
    objective = os.getenv("E2E_OBJECTIVE", "day7_retention")
    result = orchestrator.run(objective=objective, experiment_id=experiment_id)
    print(
        json.dumps(
            {
                "validation_decision": result.validation_report.get("decision"),
                "evaluation_source": result.evaluation.get("source"),
                "top_recommendation": result.recommendation.get("top_recommendation"),
            },
            indent=2,
            default=str,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
