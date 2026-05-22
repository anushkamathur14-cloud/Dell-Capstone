"""Load system prompts from ``prompts/`` with progressive disclosure tiers."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

DisclosureLevel = Literal["minimal", "standard", "full"]

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PROMPTS_ROOT = _REPO_ROOT / "prompts"


def _read(rel_path: str) -> str:
    path = _PROMPTS_ROOT / rel_path
    if not path.exists():
        raise FileNotFoundError(f"Prompt file not found: {path}")
    return path.read_text(encoding="utf-8").strip()


def load_prompt(rel_path: str) -> str:
    """Load a single markdown prompt relative to ``prompts/``."""
    return _read(rel_path)


def load_prompt_bundle(
    agent: str,
    *,
    disclosure: DisclosureLevel = "standard",
) -> str:
    """Compose a system prompt: base + optional panels by disclosure level."""
    parts: list[str] = []

    if agent == "orchestrator":
        parts.append(_read("orchestrator/system.md"))
        if disclosure in {"standard", "full"}:
            parts.append(_read("orchestrator/skills_index.md"))
    elif agent == "validation":
        parts.append(_read("validation/validator_system.md"))
    elif agent == "causal":
        parts.append(_read("causal/system.md"))
        if disclosure in {"standard", "full"}:
            parts.append(_read("causal/statistical_analysis.md"))
        if disclosure == "full":
            parts.append(
                "Full reference: use `list_analysis_reference(detail=...)` tool for hypothesis/regression sections."
            )
    else:
        raise ValueError(f"Unknown agent prompt bundle: {agent}")

    return "\n\n---\n\n".join(parts)
