"""Pytest defaults — keep LangSmith off unless a test explicitly opts in."""

from __future__ import annotations

import os


def pytest_configure() -> None:
    os.environ.setdefault("LANGSMITH_TRACING", "false")
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")
