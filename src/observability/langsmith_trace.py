"""LangSmith-run naming conventions (stable strings for dashboards and alerts)."""


class TraceNames:
    """Use these constants for `@traceable(name=...)`, tags, or run grouping."""

    BENCHMARK_GENERATION = "benchmark_generation"
    RETRIEVAL_SKILL = "retrieval_skill"
    VALIDATION_SKILL = "validation_skill"
    CAUSAL_EVALUATION_SKILL = "causal_evaluation_skill"
    EXPERIMENT_GENERATION_SKILL = "experiment_generation_skill"
    RECOMMENDATION_AGENT_V1 = "recommendation_agent_v1"
    COORDINATOR_RUN = "coordinator_run"
    COORDINATOR_MINIMAL_DEMO = "coordinator_minimal_demo"
