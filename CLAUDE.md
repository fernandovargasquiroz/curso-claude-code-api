# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

Dependency and tooling manager is `uv`. Python is pinned to the 3.12 series
(`pyproject.toml`).

`README.md` is the canonical, single walkthrough for install/test/lint/run —
read it before assuming a command; don't duplicate its contents here.

- Run a single test: `uv run pytest tests/test_health.py::test_health_returns_ok -q`
- Validate `compose.yaml` without needing a `.env` file (only when touching
  `compose.yaml` or `.env.example`): `docker compose config -q`

## Architecture

- ASGI entrypoint: `app/main.py` exposes `app = FastAPI()` as `app.main:app`.
  Today the only implemented route is `GET /health`; the rest of the API
  surface described below is contract, not yet code.
- `compose.yaml` declares a single `db` service (`postgres:18-alpine`) with a
  healthcheck and a named volume mounted at `/var/lib/postgresql` (not the
  default `/var/lib/postgresql/data`). It renders with `docker compose config`
  without requiring a `.env` file — all `POSTGRES_*` variables have inline
  defaults matching `.env.example`.
- `alembic/` holds migrations; `app/database.py::get_database_url()` builds the
  connection URL from the same `POSTGRES_*` env vars (loaded via
  `python-dotenv`, never read directly), defaulting host to `localhost`
  since the API runs on the host, not in a container. `alembic/env.py` calls
  it instead of reading `sqlalchemy.url` from `alembic.ini`. The first
  migration creates and seeds the fixed `states` catalog — see
  `docs/contrato-api.md`.

## Repository state

Documentation drives implementation here: `docs/contrato-api.md` specifies the
full target API (health, states catalog, projects, tasks v1, tasks v2 due
dates, exact response schemas, deterministic list ordering, Unicode-aware
title normalization) before that behavior exists in code. Read it before
adding or changing any endpoint.

## Engineering decisions (`docs/decisiones-ingenieria.md`)

This file is the team's source of truth for decisions that cannot be inferred
from code. Treat it as binding, not as a suggestion — a proposal that
conflicts with it (e.g. `evidencias/propuesta-atajo.md`, an example of exactly
this kind of conflict) should not be followed without reconciling it with
these rules first:

- **API contract**: `docs/contrato-api.md` defines observable behavior. Only
  change it when a ticket explicitly says the contract changes.
- **Commands**: `README.md` is the canonical source for install/test/lint/run
  commands. Don't duplicate them in this file.
- **Database**: persistence tests run against PostgreSQL, never SQLite —
  SQLite does not reproduce the same constraints, types, or migrations.
  Schema changes go through Alembic migrations (no side-effect schema
  creation on import). Every migration implements both `upgrade` and
  `downgrade` and is tested in both directions before merging.
- **Tests**: a new capability starts with a test that fails because the
  capability is missing. Never weaken or delete an existing test to turn it
  green — if the agreed behavior changed, update the contract first, then the
  test, in a separate commit.
- **Local secrets**: never open, print, edit, or commit `.env` — it may
  contain secrets. `.env.example` is the only permitted source for variable
  names; real values are configured outside the conversation.
