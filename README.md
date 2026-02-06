# Core-Rag

## Using uv (Python package manager)

The project is configured with `pyproject.toml` and works best with `uv`.

### 1) Install uv
[Installation instruction](https://docs.astral.sh/uv/reference/installer/)

### 2) Create the environment and install deps
- First time setup: `uv sync`
  - Creates `.venv` and an `uv.lock` file based on `pyproject.toml`.
- You usually don’t need to activate the venv manually; use `uv run`.

### 3) Add or remove dependencies
- Runtime deps: `uv add <package>`
- Dev-only deps: `uv add --group dev <package>`
- Remove: `uv remove <package>`

## Pre-commit Hooks

Enable Git hooks to catch common issues before committing.

- Install dev tools (once): `uv sync --group dev`
- Install hooks: `uv run pre-commit install`
- Run on all files (optional): `uv run pre-commit run --all-files`

Configuration: `.pre-commit-config.yaml`. To upgrade hooks later, run
`uv run pre-commit autoupdate`.
