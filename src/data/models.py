"""Pydantic data contracts for experimentation objects."""

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class Experiment(BaseModel):
    experiment_id: str
    objective: str
    start_date: datetime | None = None
    end_date: datetime | None = None
    status: str
    traffic_split: dict[str, float] = Field(default_factory=dict)
    owner: str | None = None
    notes: str | None = None


class ArmVariant(BaseModel):
    experiment_id: str
    arm_id: str
    treatment_description: str
    structured_parameters_json: dict[str, Any] = Field(default_factory=dict)
    treatment_type: str
    constraints_tag: str | None = None


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
    conversion: float | None = None
    retention: float | None = None
    engagement: float | None = None
    revenue_proxy: float | None = None
    variance: float | None = None
    confidence_interval: list[float] = Field(default_factory=list)


class ExperimentMemory(BaseModel):
    experiment_id: str
    summary_text: str
    lessons_learned: list[str] = Field(default_factory=list)
    winning_patterns: list[str] = Field(default_factory=list)
    failed_patterns: list[str] = Field(default_factory=list)
    analyst_notes: str | None = None
