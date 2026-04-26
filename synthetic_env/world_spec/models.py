"""Typed schema definitions for synthetic world specification."""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class SegmentSpec(BaseModel):
    id: str
    share: float = Field(ge=0.0, le=1.0)
    baseline_skill_mean: float = Field(ge=0.0, le=1.0)
    engagement_propensity_mean: float = Field(ge=0.0, le=1.0)
    spend_propensity_mean: float = Field(ge=0.0, le=1.0)
    friction_tolerance_mean: float = Field(ge=0.0, le=1.0)


class ParameterSpec(BaseModel):
    type: Literal["continuous", "categorical"]
    min: float | None = None
    max: float | None = None
    values: list[str] | None = None


class ArmSpec(BaseModel):
    difficulty_shift: float
    reward_rate: float
    matchmaking_delay_sec: float
    ui_friction: float
    progression_speed: float
    content_exposure_intensity: float
    onboarding_support: str
    promotion_intensity: str
    constraints_tag: str


class KPIConfig(BaseModel):
    type: str
    timing: str
    optimize_directly: bool = False


class WorldSpec(BaseModel):
    meta: dict[str, Any]
    segments: list[SegmentSpec]
    user_attributes: dict[str, Any]
    treatment_parameters: dict[str, ParameterSpec]
    example_arms: dict[str, ArmSpec]
    constraints: dict[str, Any]
    kpis: dict[str, KPIConfig]
    causal_assumptions: dict[str, Any]
    realism_levels: dict[str, Any]
