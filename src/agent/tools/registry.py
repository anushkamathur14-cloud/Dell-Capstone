"""Central registry: deep agents invoke capabilities only through *Skill classes."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional

from src.skills.causal_evaluation import CausalEvaluationSkill
from src.skills.experiment_generation import ExperimentGenerationSkill
from src.skills.recommendation import RecommendationSkill
from src.skills.retrieval import RetrievalSkill
from src.skills.statistical_analysis import StatisticalAnalysisSkill
from src.skills.validation import ValidationSkill


@dataclass
class ToolSpec:
    name: str
    description: str
    handler: Callable[..., Any]


class SkillRegistry:
    """Exposes skills as named tools (≤10 per agent recommended)."""

    def __init__(
        self,
        retrieval: Optional[RetrievalSkill] = None,
        validation: Optional[ValidationSkill] = None,
        causal: Optional[CausalEvaluationSkill] = None,
        generation: Optional[ExperimentGenerationSkill] = None,
        recommendation: Optional[RecommendationSkill] = None,
        statistical_analysis: Optional[StatisticalAnalysisSkill] = None,
    ) -> None:
        self.retrieval = retrieval or RetrievalSkill()
        self.validation = validation or ValidationSkill()
        self.causal = causal or CausalEvaluationSkill()
        self.generation = generation or ExperimentGenerationSkill()
        self.recommendation = recommendation or RecommendationSkill()
        self.statistical_analysis = statistical_analysis or StatisticalAnalysisSkill()
        self._tools: dict[str, ToolSpec] = {}
        self._register_defaults()

    def _register(self, name: str, description: str, handler: Callable[..., Any]) -> None:
        self._tools[name] = ToolSpec(name=name, description=description, handler=handler)

    def _register_defaults(self) -> None:
        self._register(
            "retrieval_skill",
            "Load experiment context (experiment, arms, metrics, memory).",
            self.retrieval.run,
        )
        self._register(
            "validation_skill",
            "Run full validation pipeline; returns ValidationReport dict.",
            self.validation.run,
        )
        self._register(
            "causal_evaluation_skill",
            "Programmatic difference-in-means causal estimate from metrics.",
            self.causal.run_programmatic,
        )
        self._register(
            "causal_design_experiment_skill",
            "Propose statistical experiment design (arms, sample size, metric).",
            self.causal.design_experiment,
        )
        self._register(
            "causal_sandbox_analysis_skill",
            "Run extended statistical analysis code in Daytona/local sandbox.",
            self.causal.run_sandbox_analysis,
        )
        self._register(
            "experiment_generation_skill",
            "Generate schema-validated candidate experiments.",
            lambda context, evaluation: self.generation.run(context=context, evaluation=evaluation),
        )
        self._register(
            "recommendation_score_skill",
            "Score all candidates with lift_aware_v1.",
            self.recommendation.run_score,
        )
        self._register(
            "recommendation_rank_skill",
            "Rank scored candidates (canonical deterministic order).",
            self.recommendation.run_rank,
        )
        self._register(
            "statistical_analysis_skill",
            "Post-experiment statistical analysis after run completes.",
            self.statistical_analysis.run,
        )

    def list_tools(self) -> list[ToolSpec]:
        return list(self._tools.values())

    def invoke(self, name: str, **kwargs: Any) -> Any:
        if name not in self._tools:
            raise KeyError(f"Unknown tool: {name}")
        return self._tools[name].handler(**kwargs)

    def tool_catalog_for_prompt(self, allowed: list[str]) -> str:
        lines = []
        for key in allowed:
            spec = self._tools.get(key)
            if spec:
                lines.append(f"- {spec.name}: {spec.description}")
        return "\n".join(lines)


_default_registry: Optional[SkillRegistry] = None


def get_skill_registry(registry: Optional[SkillRegistry] = None) -> SkillRegistry:
    global _default_registry
    if registry is not None:
        return registry
    if _default_registry is None:
        _default_registry = SkillRegistry()
    return _default_registry
