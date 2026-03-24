---
name: validate-code
description: >-
  Run linting, formatting, type-checking, and unit tests for the http_py
  codebase using pre-commit.  Use this skill whenever you need to validate
  that code changes pass all quality gates before committing or pushing.
---

# Validate Code

## When to Use

- After editing any Python file in the repository.
- Before committing or creating a pull request.
- When the user asks to "lint", "check", "validate", or "type-check" code.

## Command

Run **all** pre-commit hooks (ruff lint + format, mypy, unit tests on push):

```bash
poetry run pre-commit run --all-files
```

## What It Checks

The `.pre-commit-config.yaml` defines these hooks:

| Hook | Stage | What it does |
|------|-------|--------------|
| **ruff (fix)** | pre-commit | Auto-fixes lint issues (except E501 line length) |
| **ruff-format** | pre-commit | Enforces consistent formatting (Black-compatible) |
| **ruff (E501)** | pre-commit | Fails on remaining line-length violations |
| **mypy** | pre-commit | Static type-checking across `http_py/` |
| **unittests** | pre-push | Runs `python -m unittest discover -v` |

> **Note:** The `unittests` hook only runs on `pre-push` stage by default.
> To include it during local validation, run:
>
> ```bash
> poetry run pre-commit run --all-files --hook-stage pre-push
> ```

## Interpreting Failures

1. **ruff lint / format** — If ruff auto-fixed files, they will show as
   "Failed" but the fixes are already applied. Re-run the command to confirm
   a clean pass.
2. **mypy** — Type errors must be resolved manually. Read the mypy output
   for file paths and line numbers.
3. **unittests** — Test failures include tracebacks. Fix the failing test or
   the code under test.

## Quick Individual Commands

```bash
# Format only
poetry run ruff format .

# Lint with auto-fix
poetry run ruff check --fix .

# Lint check only (no fix)
poetry run ruff check .

# Type-check only
poetry run mypy http_py

# Unit tests only
poetry run python -m unittest discover -v
```
