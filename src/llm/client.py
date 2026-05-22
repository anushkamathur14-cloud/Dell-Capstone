"""Shared chat LLM factory for OpenAI API or Azure AI Foundry deployments.

Set AZURE_OPENAI_ENDPOINT + AZURE_OPENAI_API_KEY to use Foundry/Azure OpenAI.
Otherwise falls back to OPENAI_API_KEY or LANGCHAIN_API_KEY with ChatOpenAI.

Model env vars (VALIDATION_LLM_MODEL, etc.) are **deployment names** on Azure
and **model names** on direct OpenAI — keep them aligned with your Foundry project.
"""

from __future__ import annotations

import os
from typing import Any, Literal

LlmProvider = Literal["azure", "openai"]


def _provider() -> LlmProvider:
    explicit = (os.getenv("LLM_PROVIDER") or "auto").strip().lower()
    if explicit == "azure":
        return "azure"
    if explicit == "openai":
        return "openai"
    if os.getenv("AZURE_OPENAI_ENDPOINT"):
        return "azure"
    return "openai"


def llm_provider_label() -> str:
    return _provider()


def is_llm_configured() -> bool:
    if _provider() == "azure":
        return bool(os.getenv("AZURE_OPENAI_ENDPOINT") and os.getenv("AZURE_OPENAI_API_KEY"))
    return bool(os.getenv("OPENAI_API_KEY") or os.getenv("LANGCHAIN_API_KEY"))


def get_chat_llm(*, model_env: str, default_model: str = "gpt-4o-mini", temperature: float = 0) -> Any:
    """Return a LangChain chat model for the given model/deployment env var."""
    model_or_deployment = os.getenv(model_env, default_model)

    if _provider() == "azure":
        from langchain_openai import AzureChatOpenAI

        endpoint = os.getenv("AZURE_OPENAI_ENDPOINT")
        api_key = os.getenv("AZURE_OPENAI_API_KEY")
        if not endpoint or not api_key:
            raise RuntimeError(
                "Azure LLM selected but AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_API_KEY is missing."
            )
        return AzureChatOpenAI(
            azure_deployment=model_or_deployment,
            api_version=os.getenv("AZURE_OPENAI_API_VERSION", "2024-08-01-preview"),
            azure_endpoint=endpoint.rstrip("/"),
            api_key=api_key,
            temperature=temperature,
        )

    from langchain_openai import ChatOpenAI

    api_key = os.getenv("OPENAI_API_KEY") or os.getenv("LANGCHAIN_API_KEY")
    if not api_key:
        raise RuntimeError("OpenAI LLM selected but no OPENAI_API_KEY or LANGCHAIN_API_KEY is set.")
    return ChatOpenAI(model=model_or_deployment, temperature=temperature, api_key=api_key)
