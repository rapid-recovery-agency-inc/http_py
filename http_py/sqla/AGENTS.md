# SQLAlchemy Module

## Purpose

This module provides the opt-in SQLAlchemy integration path for `http_py`. It adapts SQLAlchemy async engines to the shared context and connection-pool-like seam used by request logging, rate limiting, and database-backed cache flows.

## Scope

- `adapters.py` converts SQLAlchemy async engines into seam-compatible reader and writer pool adapters.
- `context.py` exposes explicit engine-based constructors and engine-group convenience constructors for downstream applications that already own a reader or writer engine container.

## Design Rules

- Default database backing for `http_py` remains psycopg pools from `http_py.postgres`.
- SQLAlchemy support is opt-in and must not change the default psycopg API.
- Reader and writer behavior stay distinct: readers use connection scope, writers use explicit transaction scope.
- Keep tests for this module in `http_py/sqla/tests` and limit them to SQLAlchemy adapter and context seams.