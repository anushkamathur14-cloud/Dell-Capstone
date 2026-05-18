"""Optional LLM diagnostics for validation reports."""

from __future__ import annotations

import json
import os
from typing import Any


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
        use_llm = bool(os.getenv("LANGCHAIN_API_KEY") or os.getenv("OPENAI_API_KEY"))

    if not use_llm:
        return _template_summary(decision, issues, warnings, checks), "template"

    try:
        from langchain_core.messages import HumanMessage, SystemMessage
        from langchain_openai import ChatOpenAI
    except ImportError:
        return _template_summary(decision, issues, warnings, checks), "template"

    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
    model_name = os.getenv("VALIDATION_LLM_MODEL", "gpt-4o-mini")
    llm = ChatOpenAI(model=model_name, temperature=0, api_key=api_key)

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
