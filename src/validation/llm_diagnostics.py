"""Optional LLM diagnostics for validation reports.

Produces diagnostics_summary after the decide node. Falls back to a deterministic
template when ENABLE_VALIDATION_LLM is false, Azure is not configured, or
langchain-openai is unavailable. LLM text is narrative only; decision stays in code.
"""

from __future__ import annotations

import json
from typing import Any

from src.llm.azure_factory import get_azure_chat_model, validation_llm_enabled


def _template_summary(
    decision: str,
    issues: list[str],
    warnings: list[str],
    checks: list[dict[str, Any]],
) -> str:
    failed = [check for check in checks if not check["passed"]]
    lines = [
        f"Validation decision: {decision}.",
        f"Blocking issues ({len(issues)}): " + ("; ".join(issues) if issues else "none"),
        f"Warnings ({len(warnings)}): " + ("; ".join(warnings) if warnings else "none"),
    ]
    if failed:
        lines.append("Failed checks:")
        for check in failed[:8]:
            lines.append(f"- [{check['severity']}] {check['name']}: {check['message']}")
    return "\n".join(lines)


def generate_diagnostics_summary(
    decision: str,
    issues: list[str],
    warnings: list[str],
    checks: list[dict[str, Any]],
    *,
    use_llm: bool | None = None,
) -> tuple[str, str]:
    """Return (summary, source) where source is 'llm' or 'template'."""
    if use_llm is None:
        use_llm = validation_llm_enabled()

    if not use_llm:
        return _template_summary(decision, issues, warnings, checks), "template"

    try:
        from langchain_core.messages import HumanMessage, SystemMessage
    except ImportError:
        return _template_summary(decision, issues, warnings, checks), "template"

    llm = get_azure_chat_model("validation", temperature=0.0)
    if llm is None:
        return _template_summary(decision, issues, warnings, checks), "template"

    payload = {
        "decision": decision,
        "issues": issues,
        "warnings": warnings,
        "failed_checks": [check for check in checks if not check["passed"]],
    }
    messages = [
        SystemMessage(
            content=(
                "You are a data-quality analyst for adaptive experimentation. "
                "Summarize validation results in 3-5 concise sentences for a growth owner. "
                "Distinguish blocking issues from warnings. Do not invent data."
            )
        ),
        HumanMessage(content=f"Validation payload:\n{json.dumps(payload, default=str)}"),
    ]
    response = llm.invoke(messages)
    content = response.content if isinstance(response.content, str) else str(response.content)
    return content.strip(), "llm"
