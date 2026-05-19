"""Execute Python analysis in Daytona when configured; else local subprocess sandbox."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

# Broader allowlist for post-experiment / causal sandbox analysis
ALLOWED_IMPORTS = (
    "pandas",
    "numpy",
    "scipy",
    "statsmodels",
    "sklearn",
    "math",
    "json",
    "statistics",
)


def _run_local_sandbox(code: str, payload: dict[str, Any], timeout_sec: int = 60) -> dict[str, Any]:
    script = f"""
import json
import math
import statistics

payload = json.loads({json.dumps(json.dumps(payload))})

{code}

if "result" not in dir():
    result = {{"status": "ok", "note": "no result variable set"}}
print("__SANDBOX_RESULT__" + json.dumps(result))
"""
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "analysis.py"
        path.write_text(script, encoding="utf-8")
        try:
            proc = subprocess.run(
                [sys.executable, str(path)],
                capture_output=True,
                text=True,
                timeout=timeout_sec,
                cwd=tmp,
                env={**os.environ, "PYTHONPATH": ""},
            )
        except subprocess.TimeoutExpired:
            return {"status": "error", "source": "local_subprocess", "error": "timeout"}

        stdout = proc.stdout or ""
        marker = "__SANDBOX_RESULT__"
        if marker in stdout:
            raw = stdout.split(marker, 1)[1].strip().split("\n")[0]
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = {"raw": raw}
            return {
                "status": "ok" if proc.returncode == 0 else "error",
                "source": "local_subprocess",
                "result": parsed,
                "stderr": proc.stderr[-2000:] if proc.stderr else "",
            }
        return {
            "status": "error",
            "source": "local_subprocess",
            "error": proc.stderr or "no result marker",
            "stdout": stdout[-2000:],
        }


def _run_daytona(code: str, payload: dict[str, Any]) -> dict[str, Any]:
    api_key = os.getenv("DAYTONA_API_KEY")
    if not api_key:
        return {"status": "skipped", "source": "daytona", "reason": "DAYTONA_API_KEY not set"}

    try:
        from daytona import Daytona, DaytonaConfig  # type: ignore[import-untyped]
    except ImportError:
        return {
            "status": "skipped",
            "source": "daytona",
            "reason": "daytona package not installed; pip install daytona",
        }

    config = DaytonaConfig(api_key=api_key)
    daytona = Daytona(config)
    sandbox = daytona.create()
    try:
        full_code = (
            "import json\n"
            f"payload = json.loads({json.dumps(json.dumps(payload))})\n"
            f"{code}\n"
            "if 'result' not in dir():\n"
            '    result = {"status": "ok"}\n'
            "print(json.dumps(result))\n"
        )
        response = sandbox.process.code_run(full_code)
        output = getattr(response, "result", None) or str(response)
        try:
            parsed = json.loads(output)
        except (json.JSONDecodeError, TypeError):
            parsed = {"raw": output}
        return {"status": "ok", "source": "daytona", "result": parsed}
    except Exception as exc:  # pragma: no cover - network/SDK dependent
        return {"status": "error", "source": "daytona", "error": str(exc)}
    finally:
        try:
            sandbox.delete()
        except Exception:
            pass


def run_python_in_sandbox(code: str, payload: dict[str, Any]) -> dict[str, Any]:
    """Prefer Daytona; fall back to local subprocess. Programmatic path unaffected."""
    prefer_daytona = os.getenv("SANDBOX_PROVIDER", "daytona").lower() == "daytona"
    if prefer_daytona and os.getenv("DAYTONA_API_KEY"):
        outcome = _run_daytona(code, payload)
        if outcome.get("status") not in ("skipped", "error"):
            return outcome
    return _run_local_sandbox(code, payload)
