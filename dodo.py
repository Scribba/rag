"""Doit tasks for this repository.

Includes an initial task to run unit tests.

Usage:
- `uv run doit test` (recommended with uv)
- Or activate your venv and run `doit test`
"""

from __future__ import annotations
from typing import Dict


def task_test() -> Dict[str, object]:
    return {
        "actions": ["uv run pytest"],
        "verbosity": 2,
        "doc": "Run unit tests (pytest preferred)",
    }


def task_mypy() -> Dict[str, object]:
    return {
        "actions": ["uv run mypy src/"],
        "verbosity": 2,
        "doc": "Run mypy type checks",
    }
