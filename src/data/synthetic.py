"""Scaffold for realistic synthetic experiment data generation."""

from dataclasses import dataclass
from typing import Any

import pandas as pd


@dataclass
class SyntheticGenerationSpec:
    """Spec grounded in schema, treatments, metric logic, and contexts."""

    experiment_schema: dict[str, Any]
    treatment_parameter_table: pd.DataFrame
    metric_logic: dict[str, Any]
    segment_context_table: pd.DataFrame
    random_seed: int = 42


class SyntheticDataGenerator:
    """Placeholder generator for credible synthetic experimentation data."""

    def __init__(self, spec: SyntheticGenerationSpec) -> None:
        self.spec = spec

    def generate_experiments(self, n_experiments: int = 10) -> pd.DataFrame:
        """Generate experiment-level records from schema placeholders."""
        return pd.DataFrame(
            {
                "experiment_id": [f"exp_{idx:03d}" for idx in range(n_experiments)],
                "objective": ["improve_retention"] * n_experiments,
                "status": ["completed"] * n_experiments,
            }
        )

    def generate_observations(self, experiment_id: str, n_rows: int = 1000) -> pd.DataFrame:
        """Generate observation-level placeholders with segment context hooks."""
        return pd.DataFrame(
            {
                "entity_id": [f"user_{i:06d}" for i in range(n_rows)],
                "experiment_id": [experiment_id] * n_rows,
                "arm_id": ["control"] * n_rows,
                "conversion": [0] * n_rows,
            }
        )
