# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Python client library for the **MATBA ROFEX Primary API v1.21** — a REST API for electronic trading on Argentina's derivatives and securities exchange. The library wraps all REST endpoints (segments, instruments, orders, market data, risk) into simple Python functions with automatic token management.

## Development Commands

```bash
# Install dependencies (uses uv)
uv sync

# Run the example script
uv run python main.py
```

There are no tests, linter, or formatter configured yet. Python 3.12+ is required (see `.python-version`).

## Architecture

The library is a **single-module stateful client** (`matriz_client/`) with module-level globals for auth state:

- **`client.py`** — All API logic. Uses module-level `_token`, `_session`, and `_base_url` globals. Token auto-refreshes before 24h expiry via `_ensure_token()`. Two auth modes:
  - **Token auth** (most endpoints): `X-Auth-Token` header, obtained via `POST /auth/getToken`
  - **HTTP Basic Auth** (Risk API only): uses `PRIMARY_USER`/`PRIMARY_PASSWORD` directly
- **`__init__.py`** — Re-exports all public functions as a flat namespace (`import matriz_client as primary`)
- **`exceptions.py`** — `PrimaryAPIError` and `AuthenticationError`

All API calls go through `_request()` → `_get()` helpers. The API uses GET for everything, including order submission (this is how the Primary API works, not a bug).

## Configuration

Environment variables loaded from `.env` via `python-dotenv`:
- `PRIMARY_USER` — API username (required)
- `PRIMARY_PASSWORD` — API password (required)
- `PRIMARY_BASE_URL` — defaults to `https://api.remarkets.primary.com.ar`

## API Reference

The full Primary API v1.21 specification is in `primary_api_llm.md` (LLM-optimized markdown). Use this as the authoritative reference when adding endpoints or debugging API behavior. Key concepts:
- `clOrdId` identifies a request; `orderId` identifies the order in the exchange
- Market segments: `DDF` (financial derivatives), `DDA` (agricultural), `DUAL`, `MERV` (external markets)
- Market data entries: `BI` (bid), `OF` (offer), `LA` (last), `OP` (open), `CL` (close), `SE` (settlement), `OI` (open interest)

## External References

- **Linear team**: `Becerra` (prefix `BEC`). Use the Linear MCP to read/create/update issues.
- **Obsidian vault**: `./matriz-vault/` — accessible via the `obsidian` MCP server. Contains:
  - `projects/matriz-client/` — project-specific notes (domain, ADRs, runbooks)
  - `knowledge/` — cross-project knowledge (Python, architecture, tools)
  - `workflows/` — documented workflows
- **GitHub**: repo `sebadlf/matriz-client`. Use the `github` MCP for PRs, issues, reviews.

## Git Conventions

- **Branch format**: `sebadlf-bec-{issue-number}-{short-description}` (copy from the Linear issue — it auto-generates this)
- **PR body**: must include the Linear issue ID (e.g., `BEC-7`) — triggers auto-link in Linear
- **Never commit directly to `main`** — protected branch, PR required
- **CI must pass** before merge: Ruff lint + format check (`.github/workflows/ci.yml`)

## Workflow

Para issues nuevos, el flujo es:

1. Leer el issue en Linear (via MCP) para entender el contexto
2. Consultar notas de dominio relevantes en `matriz-vault/` (via obsidian MCP) si aplica
3. Crear branch con el formato correcto
4. Implementar, correr Ruff localmente (`uv run ruff check . && uv run ruff format .`)
5. Commitear y crear PR con link al issue de Linear
6. Merge → Linear auto-cierra el issue
