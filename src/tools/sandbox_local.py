"""Local isolated Python execution (capstone sandbox; not production-hardened)."""

from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path


def execute_python_in_sandbox(code: str, *, timeout_seconds: int = 30) -> dict[str, str | int]:
    """Run Python code in a temp directory; return stdout/stderr and exit code."""
    with tempfile.TemporaryDirectory(prefix="capstone_sandbox_") as tmp:
        script = Path(tmp) / "analysis.py"
        script.write_text(code, encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            timeout=timeout_seconds,
            cwd=tmp,
        )
    return {
        "exit_code": proc.returncode,
        "stdout": proc.stdout[-8000:],
        "stderr": proc.stderr[-4000:],
    }
