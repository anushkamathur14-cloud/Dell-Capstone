"""Load repo .env."""

from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def load_env() -> Path | None:
    env_path = ROOT / ".env"
    if not env_path.exists():
        return None
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        key, val = k.strip(), v.strip()
        # Shell/Cursor often exports empty LANGSMITH_* / AZURE_* — prefer .env when set.
        if val and not os.environ.get(key, "").strip():
            os.environ[key] = val
        else:
            os.environ.setdefault(key, val)
    return env_path
