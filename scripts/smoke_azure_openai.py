#!/usr/bin/env python3
"""Opt-in smoke test: ping each Azure OpenAI deployment with a trivial prompt.

Not part of pytest/CI. Run only when credentials are configured locally:

  RUN_AZURE_OPENAI_SMOKE=true python scripts/smoke_azure_openai.py

Requires: pip install -e ".[llm]" and a .env with AZURE_OPENAI_* set.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT))


def _load_dotenv() -> None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key, value = key.strip(), value.strip()
        if key:
            os.environ[key] = value


def _check_endpoint_dns(endpoint: str) -> str | None:
    from urllib.parse import urlparse

    host = urlparse(endpoint).hostname
    if not host:
        return "AZURE_OPENAI_ENDPOINT is not a valid URL."
    try:
        import socket

        socket.getaddrinfo(host, 443)
    except socket.gaierror:
        return (
            f"Cannot resolve host '{host}'. Copy the exact endpoint from Azure AI Foundry "
            "(often https://<resource>.openai.azure.com/)."
        )
    return None


def main() -> int:
    if os.getenv("RUN_AZURE_OPENAI_SMOKE", "false").lower() not in {"1", "true", "yes"}:
        print("Set RUN_AZURE_OPENAI_SMOKE=true to run this script.")
        return 0

    _load_dotenv()

    from langchain_core.messages import HumanMessage
    from src.llm.azure_factory import SkillRole, get_azure_chat_model, is_azure_configured

    if not is_azure_configured():
        print("Missing AZURE_OPENAI_ENDPOINT or AZURE_OPENAI_API_KEY.")
        return 1

    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "")
    dns_err = _check_endpoint_dns(endpoint)
    if dns_err:
        print(dns_err)
        return 1
    print(f"Endpoint: {endpoint}")

    roles: list[SkillRole] = ["validation", "generation", "stat"]
    ok = 0
    for role in roles:
        llm = get_azure_chat_model(role, temperature=0.0)
        if llm is None:
            print(f"[{role}] SKIP — langchain-openai not installed")
            continue
        try:
            out = llm.invoke([HumanMessage(content="Reply with exactly: ok")])
            text = out.content if isinstance(out.content, str) else str(out.content)
            print(f"[{role}] OK — {text[:80]!r}")
            ok += 1
        except Exception as exc:
            print(f"[{role}] FAIL — {exc}")

    print(f"\n{ok}/{len(roles)} deployments responded.")
    return 0 if ok == len(roles) else 1


if __name__ == "__main__":
    raise SystemExit(main())
