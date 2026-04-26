"""Load and validate world specification from YAML."""

from __future__ import annotations

from pathlib import Path

import yaml

from synthetic_env.world_spec.models import WorldSpec


def load_world_spec(path: str | Path = "configs/world_spec.yaml") -> WorldSpec:
    raw = yaml.safe_load(Path(path).read_text(encoding="utf-8"))
    return WorldSpec.model_validate(raw)
