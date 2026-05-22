"""Azure OpenAI chat model factory by capstone skill role.

Deployment names (capstone-mini, capstone-standard, capstone-code) are configured
via environment variables. Secrets are never hardcoded.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, Literal

from src.config.settings import get_settings

if TYPE_CHECKING:
    from langchain_openai import AzureChatOpenAI

SkillRole = Literal["validation", "generation", "stat"]

_ROLE_DEPLOYMENT_ENV: dict[SkillRole, str] = {
    "validation": "VALIDATION_LLM_MODEL",
    "generation": "GENERATION_LLM_MODEL",
    "stat": "STAT_LLM_MODEL",
}

_DEFAULT_DEPLOYMENTS: dict[SkillRole, str] = {
    "validation": "capstone-mini",
    "generation": "capstone-standard",
    "stat": "capstone-code",
}


def _env(name: str) -> str | None:
    value = os.getenv(name)
    return value.strip() if value else None


def is_azure_configured() -> bool:
    return bool(_env("AZURE_OPENAI_ENDPOINT") and _env("AZURE_OPENAI_API_KEY"))


def validation_llm_enabled() -> bool:
    settings = get_settings()
    return bool(settings.enable_validation_llm) and is_azure_configured()


def get_deployment_name(role: SkillRole) -> str:
    env_key = _ROLE_DEPLOYMENT_ENV[role]
    return _env(env_key) or _DEFAULT_DEPLOYMENTS[role]


def _azure_runtime_config() -> tuple[str, str, str] | None:
    endpoint = _env("AZURE_OPENAI_ENDPOINT")
    api_key = _env("AZURE_OPENAI_API_KEY")
    api_version = _env("AZURE_OPENAI_API_VERSION") or "2024-12-01-preview"
    if not endpoint or not api_key:
        return None
    return endpoint, api_key, api_version


def _deployment_supports_zero_temperature(role: SkillRole, deployment: str) -> bool:
    """Reasoning deployments (e.g. o4-mini / capstone-code) reject temperature=0 on Azure."""
    if role == "stat":
        return False
    lowered = deployment.lower()
    return not (lowered.startswith("o4") or lowered.startswith("o3") or "o4-" in lowered)


def get_azure_chat_model(
    role: SkillRole,
    *,
    temperature: float = 0.0,
) -> AzureChatOpenAI | None:
    """Return an Azure chat client for the given skill role, or None if not configured."""
    runtime = _azure_runtime_config()
    if runtime is None:
        return None

    try:
        from langchain_openai import AzureChatOpenAI
    except ImportError:
        return None

    endpoint, api_key, api_version = runtime
    deployment = get_deployment_name(role)

    kwargs: dict[str, object] = {
        "azure_endpoint": endpoint,
        "api_key": api_key,
        "api_version": api_version,
        "azure_deployment": deployment,
    }
    if _deployment_supports_zero_temperature(role, deployment):
        kwargs["temperature"] = temperature

    return AzureChatOpenAI(**kwargs)
