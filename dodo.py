"""Project tasks for doit.

Initial task set includes a `mypy` type-check task.

Usage:
- With uv: `uv run doit mypy`
- Without uv: activate your venv and run `doit mypy`
"""

from __future__ import annotations

import os
import subprocess
import sys
from typing import Dict


def _ensure_pythonpath(env: dict[str, str]) -> dict[str, str]:
    env = dict(env)
    src_abs = os.path.abspath("src")
    current = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src_abs, current]) if current else src_abs
    return env


def run_mypy() -> None:
    env = _ensure_pythonpath(os.environ.copy())
    cmd = [sys.executable, "-m", "mypy", "."]
    proc = subprocess.run(cmd, env=env)
    if proc.returncode != 0:
        raise SystemExit(proc.returncode)


def task_mypy() -> Dict[str, object]:
    """Type-check the repository with mypy."""
    return {
        "actions": [run_mypy],
        "verbosity": 2,
        "doc": "Run mypy type checks",
    }

