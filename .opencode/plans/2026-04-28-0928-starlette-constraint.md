# Starlette Dependency Constraint Upgrade Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Relax `http_py`'s Starlette version bound so downstream services can resolve Starlette 1.0.0 and eliminate the Python 3.14 deprecation warnings without changing library behavior.

**Architecture:** This is a dependency-only change in the package metadata, with a lockfile refresh to keep installs reproducible. The source tree already imports Starlette directly in middleware, request/response helpers, and exception utilities, so the main risk is resolver churn or an unexpected API regression at runtime rather than code structure changes.

**Tech Stack:** Poetry, Starlette, pytest, ruff, mypy.

---

## Objective
Update `http_py` to allow Starlette 1.x resolution, lock to a Starlette 1.0.0-compatible set of dependencies, and prove the package still installs and tests cleanly.

## Context
- Repo facts:
  - `pyproject.toml` currently pins `starlette = "^0.45.0"`, which blocks Starlette 1.x.
  - `poetry.lock` currently resolves `starlette` to `0.45.3`.
  - Direct Starlette imports live in `http_py/context.py`, `http_py/requests/services.py`, `http_py/request_logger/services.py`, `http_py/rate_limiter/services.py`, `http_py/exceptions/services.py`, `http_py/exceptions/types.py`, `http_py/exceptions/utils.py`, and `http_py/hmac/types.py`.
  - The repo has `pytest`, `ruff`, and `mypy` configured already.
- User constraints:
  - Keep the change minimal.
  - Allow downstream services to upgrade Starlette past 0.x at their own pace.
  - Verify the package still works under Python 3.14.
- Assumptions:
  - Starlette 1.0.0 remains compatible with the public APIs this library uses.
  - No source code edits are needed unless the lockfile or tests expose a real incompatibility.

## Dependency Groups

### Group 0 — Prep / Decisions
| ID | Task | Areas | Acceptance | Depends | parallel-safe | blocks |
|---|---|---|---|---|---|---|
| G0-T1 | Confirm the change is metadata-only and map the Starlette touchpoints before editing anything. | `pyproject.toml`, `poetry.lock`, `http_py/context.py`, `http_py/requests/services.py`, `http_py/request_logger/services.py`, `http_py/rate_limiter/services.py`, `http_py/exceptions/services.py`, `http_py/exceptions/types.py`, `http_py/exceptions/utils.py`, `http_py/hmac/types.py` | The plan has an exact file list and a clear no-code-change default unless validation proves otherwise. | none | yes | G1-T1, G2-T1, G2-T2 |

### Group 1 — Dependency Bump
| ID | Task | Areas | Acceptance | Depends | parallel-safe | blocks |
|---|---|---|---|---|---|---|
| G1-T1 | Update the Starlette constraint and refresh the lockfile so Poetry resolves Starlette 1.0.0. | `pyproject.toml`, `poetry.lock` | `pyproject.toml` uses `starlette = ">=0.40.0,<1.0.1"`; `poetry.lock` records `starlette` at `1.0.0`; the lockfile diff is limited to the expected resolver churn. | G0-T1 | no | G2-T1, G2-T2 |

### Group 2 — Verification / Consumer Smoke Check
| ID | Task | Areas | Acceptance | Depends | parallel-safe | blocks |
|---|---|---|---|---|---|---|
| G2-T1 | Reinstall and run the local quality gate to catch any incompatibility introduced by the new Starlette resolution. | local env, `pytest`, `ruff`, `mypy` | `poetry install` succeeds, `pytest` passes, `ruff check .` passes, and `mypy` passes with no new Starlette-related failures. | G1-T1 | no | none |
| G2-T2 | Smoke-test one downstream consumer that depends on `http_py` to confirm the warning noise is gone. | downstream repo, e.g. `lpr-classifier-microservice` | The downstream service updates `http-py` plus Starlette, test suites pass, and the Starlette deprecation warnings from `asyncio.iscoroutinefunction` no longer appear. | G1-T1 | yes | none |

## Parallel Handoff Map
- Run together: `G2-T1` and `G2-T2` can run in parallel once the lockfile is updated.
- Must sequence: `G0-T1` → `G1-T1` → validation tasks.

## Validation
- Commands:
  - `poetry install`
  - `pytest`
  - `ruff check .`
  - `mypy`
- Manual checks:
  - Confirm `poetry.lock` resolves `starlette` to `1.0.0`.
  - Confirm the local test run has no Starlette deprecation warnings.
  - In one downstream consumer, run the dependency update flow and verify warnings disappear from its test output.
- Regression checks:
  - Re-run any middleware-heavy tests if the lockfile pulls in transitive dependency changes.
  - Watch for typing drift in the Starlette middleware and response helpers.

## Risks
- Risk: Poetry resolves a Starlette 1.x set that pulls in transitive dependency changes with unexpected behavior.
  - Mitigation: keep the source diff to dependency metadata first, then gate with `pytest`, `ruff`, and `mypy`.
- Risk: A downstream service still inherits the old `<1.0.0` ceiling from an unrefreshed lockfile or stale dependency policy.
  - Mitigation: include an explicit downstream smoke check in the validation stage.
- Risk: A Starlette 1.0.0 API edge case appears in middleware or response handling.
  - Mitigation: prioritize the request logger and rate limiter paths in any follow-up regression debugging.

## Open Questions
- None blocking.

## Review Gate
User must review plan before implementation. User may approve, reject, or request changes.
