"""Validated evaluation artifact (code-owned schema, not raw LLM text)."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class EvaluationArtifact(BaseModel):
    schema_version: str = "v1.0"
    estimated_lift: float = 0.0
    placeholder_lift: float = 0.0
    uncertainty: float = Field(default=0.2, ge=0.0, le=1.0)
    segment_effects: dict[str, Any] = Field(default_factory=dict)
    ranked_directions: list[str] = Field(default_factory=list)
    analysis_notes: str = ""
    source: str = "programmatic"  # programmatic | agent_loop | stub

    def to_skill_dict(self) -> dict[str, Any]:
        data = self.model_dump()
        if data["source"] == "stub":
            data["_stub"] = True
        return data


def validate_evaluation_payload(payload: dict[str, Any]) -> EvaluationArtifact:
    """Parse and validate agent/tool output before it enters the pipeline."""
    ranked = payload.get("ranked_directions") or []
    if isinstance(ranked, str):
        ranked = [ranked]
    cleaned = {
        "schema_version": str(payload.get("schema_version") or "v1.0"),
        "estimated_lift": float(payload.get("estimated_lift") or payload.get("placeholder_lift") or 0.0),
        "placeholder_lift": float(payload.get("placeholder_lift") or payload.get("estimated_lift") or 0.0),
        "uncertainty": float(payload.get("uncertainty", 0.2)),
        "segment_effects": payload.get("segment_effects") or {},
        "ranked_directions": list(ranked),
        "analysis_notes": str(payload.get("analysis_notes") or ""),
        "source": str(payload.get("source") or "agent_loop"),
    }
    return EvaluationArtifact.model_validate(cleaned)
