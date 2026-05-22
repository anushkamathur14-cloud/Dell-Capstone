"""Unit tests for Azure LLM factory (no network calls)."""

from __future__ import annotations

import os

import pytest

from src.llm.azure_factory import (
    get_azure_chat_model,
    get_deployment_name,
    is_azure_configured,
    validation_llm_enabled,
)


@pytest.fixture(autouse=True)
def _clear_azure_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for key in (
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_API_VERSION",
        "ENABLE_VALIDATION_LLM",
        "VALIDATION_LLM_MODEL",
        "GENERATION_LLM_MODEL",
        "STAT_LLM_MODEL",
    ):
        monkeypatch.delenv(key, raising=False)


def test_deployment_defaults() -> None:
    assert get_deployment_name("validation") == "capstone-mini"
    assert get_deployment_name("generation") == "capstone-standard"
    assert get_deployment_name("stat") == "capstone-code"


def test_deployment_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("STAT_LLM_MODEL", "my-code-deploy")
    assert get_deployment_name("stat") == "my-code-deploy"


def test_not_configured_without_secrets() -> None:
    assert is_azure_configured() is False
    assert get_azure_chat_model("validation") is None
    assert validation_llm_enabled() is False


def test_validation_llm_requires_flag(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("ENABLE_VALIDATION_LLM", "false")
    assert validation_llm_enabled() is False

    monkeypatch.setenv("ENABLE_VALIDATION_LLM", "true")
    assert validation_llm_enabled() is True


def test_stat_deployment_omits_zero_temperature(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("langchain_openai")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("STAT_LLM_MODEL", "capstone-code")

    llm = get_azure_chat_model("stat")
    assert llm is not None
    # o4-style deployments must not send temperature=0
    assert getattr(llm, "temperature", None) is None or llm.temperature != 0.0


def test_get_azure_chat_model_builds_client(monkeypatch: pytest.MonkeyPatch) -> None:
    pytest.importorskip("langchain_openai")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://example.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_API_KEY", "test-key")
    monkeypatch.setenv("AZURE_OPENAI_API_VERSION", "2024-12-01-preview")
    monkeypatch.setenv("VALIDATION_LLM_MODEL", "capstone-mini")

    llm = get_azure_chat_model("validation")
    assert llm is not None
    assert llm.deployment_name == "capstone-mini"
    assert llm.temperature == 0.0
