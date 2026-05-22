"""LangChain tools for the causal evaluation agent loop."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from langchain_core.tools import StructuredTool

from src.evaluation.schema import EvaluationArtifact, validate_evaluation_payload
from src.prompts.loader import load_prompt
from src.evaluation.programmatic import run_programmatic_causal
from src.tools.sandbox_local import execute_python_in_sandbox


@dataclass
class CausalToolState:
    context: dict[str, Any]
    baseline: EvaluationArtifact | None = None
    submitted: EvaluationArtifact | None = None


def build_causal_tools(context: dict[str, Any]) -> tuple[list[StructuredTool], CausalToolState]:
    """Tools bound to a retrieval context for one orchestration run."""
    state = CausalToolState(context=context)

    def run_programmatic_baseline() -> str:
        baseline = run_programmatic_causal(context)
        baseline["source"] = "programmatic"
        artifact = validate_evaluation_payload(baseline)
        state.baseline = artifact
        return json.dumps(artifact.model_dump(), indent=2)

    def list_analysis_reference(detail: str = "overview") -> str:
        text = load_prompt("causal/statistical_analysis.md")
        if detail == "overview":
            return text.split("## Hypothesis")[0].strip()
        if detail == "hypothesis":
            start = text.find("## Hypothesis")
            end = text.find("## Regression")
            return text[start:end].strip() if start >= 0 else text
        if detail == "regression":
            start = text.find("## Regression")
            return text[start:].strip() if start >= 0 else ""
        return text[:2000]

    def execute_analysis_code(code: str) -> str:
        result = execute_python_in_sandbox(code)
        return json.dumps(result, indent=2)

    def submit_evaluation(evaluation_json: str) -> str:
        try:
            payload = json.loads(evaluation_json)
        except json.JSONDecodeError as exc:
            return f"Invalid JSON: {exc}"
        try:
            artifact = validate_evaluation_payload(payload)
        except Exception as exc:
            return f"Schema validation failed: {exc}"
        state.submitted = artifact
        return "Evaluation accepted."

    tools = [
        StructuredTool.from_function(
            run_programmatic_baseline,
            name="run_programmatic_baseline",
            description="Required first step. Deterministic baseline metrics and ranked directions.",
        ),
        StructuredTool.from_function(
            list_analysis_reference,
            name="list_analysis_reference",
            description="Progressive disclosure for statistical methods. detail: overview|hypothesis|regression",
        ),
        StructuredTool.from_function(
            execute_analysis_code,
            name="execute_analysis_code",
            description="Execute Python analysis in an isolated local sandbox; returns stdout/stderr.",
        ),
        StructuredTool.from_function(
            submit_evaluation,
            name="submit_evaluation",
            description="Submit final evaluation JSON matching the required schema.",
        ),
    ]
    return tools, state


def resolve_evaluation(state: CausalToolState) -> EvaluationArtifact:
    if state.submitted is not None:
        return state.submitted
    if state.baseline is not None:
        return state.baseline
    baseline = run_programmatic_causal(state.context)
    baseline["source"] = "stub"
    return validate_evaluation_payload(baseline)
