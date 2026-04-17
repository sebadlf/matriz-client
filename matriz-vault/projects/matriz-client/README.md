---
tags: [project, fintech, trading]
status: active
repo: github.com/sebadlf/matriz-client
---

# Matriz Client

Cliente Python para la **MATBA ROFEX Primary API v1.21**. Wrappea endpoints REST + WebSocket de trading electrónico en Argentina (derivados y valores).

## Links

- Repo: `github.com/sebadlf/matriz-client` (local: `~/development/becerra/matriz-client`)
- API spec: `primary_api_llm.md` en el repo
- Linear team: `Becerra` (prefix `BEC`) — https://linear.app/gravity-code/team/BEC
- Branch format: `sebadlf-bec-{n}-{descripcion}`
- Distribución: GitHub Releases (no PyPI), workflow `release.yml` por tag `v*`

## Estado actual

- Single-module stateful client con globals para auth (REST + WS).
- Versión: `0.2.0` — modelos safe-access (dataclasses frozen) reemplazaron Pydantic / TypedDicts.
- Toolchain: `uv`, `ruff` (lint + format), `pyright` (standard), `pytest`.
- CI: lint + format + tests + pyright en cada PR.
- Dependencias: `requests`, `python-dotenv`, `websocket-client`.

## Decisiones

- [[ADR-001 — GET para todo]] — la API usa GET incluso para orders (no es un bug)
- [[ADR-002 — Safe-access dataclasses sobre Pydantic]] — por qué `0.2.0` reemplazó la primera iteración Pydantic

## Notas de dominio

- [[Conceptos Primary API]]
- [[Segmentos de mercado]]
- [[Wire format y keys opcionales]] — el patrón de respuestas parciales que motivó safe-access

## Runbooks

- [[Setup desde cero]]
- [[Cortar un release]] — bump → tag → workflow
