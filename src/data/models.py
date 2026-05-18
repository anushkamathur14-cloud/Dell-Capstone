"""Pydantic data contracts for experimentation objects."""

from __future__ import annotations

from datetime import datetime
from typing import Any, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field

ValidationDecision = Literal["go", "caution", "stop"]


class Experiment(BaseModel):
    experiment_id: str
    objective: str
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: str
    traffic_split: dict[str, float] = Field(default_factory=dict)
    owner: Optional[str] = None
    notes: Optional[str] = None


class ArmVariant(BaseModel):
    experiment_id: str
    arm_id: str
    treatment_description: str
    structured_parameters_json: dict[str, Any] = Field(default_factory=dict)
    treatment_type: str
    constraints_tag: Optional[str] = None


class Observation(BaseModel):
    entity_id: str
    experiment_id: str
    arm_id: str
    timestamp: datetime
    context_features_json: dict[str, Any] = Field(default_factory=dict)
    outcomes_json: dict[str, Any] = Field(default_factory=dict)
    exposure_flag: bool = True


class MetricsSummary(BaseModel):
    experiment_id: str
    arm_id: str
    sample_size: int
    conversion: Optional[float] = None
    retention: Optional[float] = None
    engagement: Optional[float] = None
    revenue_proxy: Optional[float] = None
    variance: Optional[float] = None
    confidence_interval: list[float] = Field(default_factory=list)


class ExperimentMemory(BaseModel):
    experiment_id: str
    summary_text: str
    lessons_learned: list[str] = Field(default_factory=list)
    winning_patterns: list[str] = Field(default_factory=list)
    failed_patterns: list[str] = Field(default_factory=list)
    analyst_notes: Optional[str] = None


class ValidationCheck(BaseModel):
    name: str
    passed: bool
    message: str
    severity: Literal["error", "warning", "info"] = "error"
    details: dict[str, Any] = Field(default_factory=dict)


class ValidationReport(BaseModel):
    schema_version: str = "v1.0"
    decision: ValidationDecision
    issues: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    checks: list[ValidationCheck] = Field(default_factory=list)
    benchmark_loaded: bool = False
    diagnostics_summary: str = ""
    diagnostics_source: Literal["template", "llm"] = "template"


class RecommendationReport(BaseModel):
    schema_version: str = "v1.0"
    ranking_method: str = "lift_aware_v1"
    top_recommendation: Optional[dict[str, Any]] = None
    ranked_candidates: list[dict[str, Any]] = Field(default_factory=list)
    explanation: str = ""
    explanation_source: Literal["template", "llm"] = "template"
    warnings: list[str] = Field(default_factory=list)


class RecommendationCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid")

    candidate_name: str
    parameter_changes: dict[str, Any] = Field(default_factory=dict)
    rationale: str
    expected_tradeoff: str
    target_segment: str
    implementation_notes: str
    signal_from_eval: str
    metric_stub: dict[str, Optional[float]] = Field(default_factory=dict)
