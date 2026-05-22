"""Prompt loader, causal tools, and evaluation schema (no LLM)."""

from __future__ import annotations

from src.data.models import Experiment, ExperimentMemory, MetricsSummary
from src.evaluation.schema import validate_evaluation_payload
from src.prompts.loader import load_prompt, load_prompt_bundle
from src.tools.causal_tools import build_causal_tools, resolve_evaluation
from src.tools.sandbox_local import execute_python_in_sandbox


def _context() -> dict:
    return {
        "experiment": Experiment(
            experiment_id="exp_test",
            objective="improve_retention",
            status="active",
            traffic_split={"control": 0.5, "treatment": 0.5},
            owner="test",
        ),
        "metrics": [
            MetricsSummary(
                experiment_id="exp_test",
                arm_id="control",
                sample_size=100,
                conversion=0.1,
                retention=0.4,
                variance=0.05,
            )
        ],
        "arms": [],
        "memory": ExperimentMemory(
            experiment_id="exp_test",
            summary_text="test",
        ),
    }


def test_load_prompt_bundle_minimal_causal() -> None:
    text = load_prompt_bundle("causal", disclosure="minimal")
    assert "run_programmatic_baseline" in text
    assert "Hypothesis testing" not in text


def test_load_prompt_bundle_full_orchestrator() -> None:
    text = load_prompt_bundle("orchestrator", disclosure="full")
    assert "retrieval_skill" in text


def test_programmatic_baseline_tool() -> None:
    tools, state = build_causal_tools(_context())
    baseline_tool = next(t for t in tools if t.name == "run_programmatic_baseline")
    out = baseline_tool.invoke({})
    assert "ranked_directions" in out
    assert state.baseline is not None
    resolved = resolve_evaluation(state)
    assert resolved.ranked_directions


def test_validate_evaluation_payload() -> None:
    art = validate_evaluation_payload(
        {
            "estimated_lift": 0.01,
            "uncertainty": 0.3,
            "ranked_directions": ["direction-a"],
            "source": "programmatic",
        }
    )
    assert art.uncertainty == 0.3


def test_sandbox_executes_simple_code() -> None:
    result = execute_python_in_sandbox("print('sandbox_ok')")
    assert result["exit_code"] == 0
    assert "sandbox_ok" in result["stdout"]
