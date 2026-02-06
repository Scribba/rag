"""Doit tasks for this repository.

Includes tasks for tests, coverage and mypy

Usage:
- `uv run doit test`
- `uv run doit mypy`
- `uv run doit coverage`
"""

from __future__ import annotations
import os
import subprocess
import sys
from typing import Dict


SRC_DIR = "src/"
TESTS_DIR = "tests/"


def _ensure_pythonpath(env: dict[str, str]) -> dict[str, str]:
    env = dict(env)
    src_abs = os.path.abspath(SRC_DIR)
    current = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = os.pathsep.join([src_abs, current]) if current else src_abs
    return env


def task_test() -> Dict[str, object]:
    return {
        "actions": ["uv run pytest"],
        "verbosity": 2,
        "doc": "Run unit tests (pytest preferred)",
    }


def _clean_coverage_artifacts() -> None:
    for p in (".coverage",):
        try:
            if os.path.exists(p):
                os.remove(p)
        except OSError:
            pass
    for d in ("htmlcov", ".tracecov", ".covrun"):
        if os.path.isdir(d):
            try:
                import shutil

                shutil.rmtree(d, ignore_errors=True)
            except Exception:
                pass


def _has_module(name: str) -> bool:
    try:
        import importlib.util as _iu

        return _iu.find_spec(name) is not None
    except Exception:
        return False


def _run_trace_summary(env: dict[str, str]) -> int:
    os.makedirs(".tracecov", exist_ok=True)
    runner_path = os.path.join(".tracecov", "_trace_runner.py")
    code = (
        "import sys, os, pkgutil, importlib\n"
        "sys.path.insert(0, os.path.abspath('src'))\n"
        "# Import top-level modules in src to include them in coverage\n"
        "if os.path.isdir('src'):\n"
        "    mods=[name for _,name,_ in pkgutil.iter_modules(['src'])]\n"
        "    for m in mods:\n"
        "        try:\n"
        "            importlib.import_module(m)\n"
        "        except Exception:\n"
        "            pass\n"
        "# Run tests if present\n"
        "if os.path.isdir('tests'):\n"
        "    try:\n"
        "        import pytest\n"
        "        raise SystemExit(pytest.main([]))\n"
        "    except Exception:\n"
        "        import unittest\n"
        "        unittest.main(module=None, argv=['unittest','discover','-s','tests'], exit=False)\n"
    )
    with open(runner_path, "w", encoding="utf-8") as f:
        f.write(code)

    trace_args = [
        sys.executable,
        "-m",
        "trace",
        "--count",
        "--summary",
        "--coverdir",
        ".tracecov",
        "--ignore-dir",
        os.pathsep.join([".venv", "__pypackages__", "build", "dist"]),
        runner_path,
    ]
    proc = subprocess.run(trace_args, env=env)
    return proc.returncode


def run_coverage() -> None:
    """Run code coverage focused on `src/` and print a report.

    Prefers coverage.py, with a fallback to the builtin trace module.
    Ensures modules under `src/` are imported so they appear in reports even if
    tests don't import them directly.
    """

    env = _ensure_pythonpath(os.environ.copy())
    _clean_coverage_artifacts()

    if _has_module("coverage"):
        # Create a small runner that imports src modules then runs tests
        os.makedirs(".covrun", exist_ok=True)
        cov_runner = os.path.join(".covrun", "_cov_runner.py")
        runner_code = (
            "import sys, os, pkgutil, importlib\n"
            "sys.path.insert(0, os.path.abspath('src'))\n"
            "if os.path.isdir('src'):\n"
            "    mods=[name for _,name,_ in pkgutil.iter_modules(['src'])]\n"
            "    for m in mods:\n"
            "        try:\n"
            "            importlib.import_module(m)\n"
            "        except Exception:\n"
            "            pass\n"
            "try:\n"
            "    import pytest\n"
            "    raise SystemExit(pytest.main([]))\n"
            "except Exception:\n"
            "    import unittest\n"
            "    unittest.main(module=None, argv=['unittest','discover','-s','tests'], exit=False)\n"
        )
        with open(cov_runner, "w", encoding="utf-8") as f:
            f.write(runner_code)

        cmd = [
            sys.executable,
            "-m",
            "coverage",
            "run",
            f"--source={SRC_DIR}",
            cov_runner,
        ]
        proc = subprocess.run(cmd, env=env)
        if proc.returncode not in (0, 5):
            raise SystemExit(proc.returncode)

        # Enforce 90% threshold; propagate failure if under threshold or no data
        rc = subprocess.run([
            sys.executable,
            "-m",
            "coverage",
            "report",
            "--fail-under=90",
            "-m",
        ], env=env).returncode
        if rc != 0:
            raise SystemExit(rc)
    else:
        # Fallback cannot enforce threshold; provide a summary and guidance
        print("coverage.py not installed; printing trace summary (threshold not enforced).\n"
              "Install dev deps with 'uv sync --group dev' to enforce 90%.")
        rc = _run_trace_summary(env)
        if rc not in (0, 5):
            raise SystemExit(rc)


def task_coverage() -> Dict[str, object]:
    return {
        "actions": [run_coverage],
        "verbosity": 2,
        "doc": "Run coverage for src/",
    }


def task_mypy() -> Dict[str, object]:
    return {
        "actions": ["uv run mypy ."],
        "verbosity": 2,
        "doc": "Run mypy type checks",
    }
