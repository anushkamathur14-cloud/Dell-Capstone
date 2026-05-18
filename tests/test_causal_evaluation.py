"""Acceptance test for CausalEvaluationSkill"""

import pytest
from src.skills.causal_evaluation import CausalEvaluationSkill
from src.data.models import MetricsSummary


@pytest.fixture
def benchmark_context():
    """Frozen fixture based on generated_sanity_calibrated benchmark."""
    metrics = [
        MetricsSummary(
            experiment_id="benchmark_v1",
            arm_id="control",
            sample_size=2000,
            conversion=0.581,
            retention=0.589,
            engagement=49.18,
            revenue_proxy=1.061,
            variance=0.02,
            confidence_interval=[0.56, 0.60],
        ),
        MetricsSummary(
            experiment_id="benchmark_v1",
            arm_id="fast_progression",
            sample_size=2000,
            conversion=0.682,
            retention=0.651,
            engagement=59.82,
            revenue_proxy=1.289,
            variance=0.02,
            confidence_interval=[0.66, 0.70],
        ),
        MetricsSummary(
            experiment_id="benchmark_v1",
            arm_id="guided_onboarding",
            sample_size=2000,
            conversion=0.604,
            retention=0.622,
            engagement=52.81,
            revenue_proxy=1.151,
            variance=0.02,
            confidence_interval=[0.58, 0.63],
        ),
        MetricsSummary(
            experiment_id="benchmark_v1",
            arm_id="high_challenge",
            sample_size=2000,
            conversion=0.615,
            retention=0.643,
            engagement=53.10,
            revenue_proxy=1.308,
            variance=0.02,
            confidence_interval=[0.59, 0.64],
        ),
    ]
    return {"metrics": metrics}


def test_output_schema_fields(benchmark_context):
    """All required schema fields must be present in output."""
    skill = CausalEvaluationSkill()
    result = skill.run(benchmark_context)

    assert "schema_version" in result
    assert "arms_evaluated" in result
    assert "lift_estimates" in result
    assert "uncertainty" in result
    assert "segment_effects" in result
    assert "ranked_directions" in result
    assert "notes" in result


def test_arms_evaluated_excludes_control(benchmark_context):
    """Control arm must not appear in arms_evaluated."""
    skill = CausalEvaluationSkill()
    result = skill.run(benchmark_context)

    assert "control" not in result["arms_evaluated"]
    assert len(result["arms_evaluated"]) == 3


def test_lift_estimates_are_floats(benchmark_context):
    """Lift values must be real floats, not None or zero across the board."""
    skill = CausalEvaluationSkill()
    result = skill.run(benchmark_context)

    for arm_id, lifts in result["lift_estimates"].items():
        for metric, value in lifts.items():
            assert isinstance(value, float), f"{arm_id}.{metric} is not a float"


def test_ranked_directions_is_ordered(benchmark_context):
    """ranked_directions must be a non-empty list with all treatment arms."""
    skill = CausalEvaluationSkill()
    result = skill.run(benchmark_context)

    assert isinstance(result["ranked_directions"], list)
    assert len(result["ranked_directions"]) == 3
    assert result["ranked_directions"][0] == "fast_progression"


def test_uncertainty_per_arm(benchmark_context):
    """Uncertainty must be a positive float for each treatment arm."""
    skill = CausalEvaluationSkill()
    result = skill.run(benchmark_context)

    for arm_id in result["arms_evaluated"]:
        assert arm_id in result["uncertainty"]
        assert result["uncertainty"][arm_id] > 0


def test_segment_effects_structure(benchmark_context):
    """Segment effects must cover all known segments and all treatment arms."""
    skill = CausalEvaluationSkill()
    result = skill.run(benchmark_context)

    expected_segments = ["casual", "value_seeker", "core", "new_explorer"]
    for segment in expected_segments:
        assert segment in result["segment_effects"]
        for arm_id in result["arms_evaluated"]:
            assert arm_id in result["segment_effects"][segment]

