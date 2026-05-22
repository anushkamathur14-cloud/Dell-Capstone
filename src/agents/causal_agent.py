"""Causal evaluation subagent: programmatic tools + optional LLM ReAct loop."""

from __future__ import annotations

import os
from typing import Any

from src.evaluation.schema import validate_evaluation_payload
from src.llm.azure_factory import get_azure_chat_model
from src.prompts.loader import DisclosureLevel, load_prompt_bundle
from src.evaluation.programmatic import run_programmatic_causal
from src.tools.causal_tools import build_causal_tools, resolve_evaluation


class CausalEvaluationAgent:
    """Agent-in-the-loop causal eval: tools first, schema-validated output."""

    def __init__(
        self,
        *,
        disclosure: DisclosureLevel | None = None,
        max_iterations: int | None = None,
    ) -> None:
        self._disclosure: DisclosureLevel = (
            disclosure
            or os.getenv("PROMPT_DISCLOSURE_LEVEL", "standard")  # type: ignore[assignment]
        )
        self._max_iterations = max_iterations or int(os.getenv("CAUSAL_AGENT_MAX_ITERATIONS", "6"))

    def run(self, context: dict[str, Any], *, use_agent_loop: bool | None = None) -> dict[str, Any]:
        if use_agent_loop is None:
            use_agent_loop = os.getenv("ENABLE_CAUSAL_AGENT_LOOP", "false").lower() in {
                "1",
                "true",
                "yes",
            }

        if not use_agent_loop:
            payload = run_programmatic_causal(context)
            payload["source"] = "stub"
            return validate_evaluation_payload(payload).to_skill_dict()

        llm = get_azure_chat_model("stat")
        if llm is None:
            payload = run_programmatic_causal(context)
            payload["source"] = "programmatic"
            return validate_evaluation_payload(payload).to_skill_dict()

        tools, state = build_causal_tools(context)
        system_prompt = load_prompt_bundle("causal", disclosure=self._disclosure)

        try:
            from langgraph.prebuilt import create_react_agent
        except ImportError:
            return resolve_evaluation(state).to_skill_dict()

        graph = create_react_agent(llm, tools, prompt=system_prompt)
        experiment_id = context["experiment"].experiment_id
        user_msg = (
            f"Evaluate experiment {experiment_id}. "
            "Call run_programmatic_baseline first, then submit_evaluation with final JSON."
        )
        if os.getenv("CAUSAL_REQUIRE_SANDBOX", "false").lower() in {"1", "true", "yes"}:
            user_msg += (
                " You MUST call execute_analysis_code with pandas code comparing all arms "
                "before submit_evaluation."
            )
        graph.invoke(
            {"messages": [{"role": "user", "content": user_msg}]},
            config={"recursion_limit": self._max_iterations},
        )

        artifact = resolve_evaluation(state)
        if state.submitted is None:
            artifact = artifact.model_copy(update={"source": "agent_loop_merged_baseline"})
        return artifact.to_skill_dict()

    @staticmethod
    def run_deep_agent(context: dict[str, Any]) -> dict[str, Any] | None:
        """Optional path when ``deepagents`` extra is installed (Microsoft Foundry pattern)."""
        try:
            from deepagents import create_deep_agent
        except ImportError:
            return None

        llm = get_azure_chat_model("stat")
        if llm is None:
            return None

        system_prompt = load_prompt_bundle("causal", disclosure="standard")
        tools, state = build_causal_tools(context)
        agent = create_deep_agent(model=llm, system_prompt=system_prompt, tools=tools)
        experiment_id = context["experiment"].experiment_id
        agent.invoke(
            {
                "messages": [
                    {
                        "role": "user",
                        "content": f"Evaluate {experiment_id}; use tools; submit_evaluation when done.",
                    }
                ]
            }
        )
        return resolve_evaluation(state).to_skill_dict()
