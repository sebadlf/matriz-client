---
tags: [project, fintech, trading]
status: active
repo: github.com/[tu-usuario]/matriz-client
---

# Matriz Client

Cliente Python para la **MATBA ROFEX Primary API v1.21**. Wrappea endpoints REST de trading electrónico en Argentina (derivados y valores).

## Links

- Repo: `github.com/sebadlf/matriz-client` (local: `~/development/becerra/matriz-client`)
- API spec: `primary_api_llm.md` en el repo
- Linear team: `Becerra` (prefix `BEC`) — https://linear.app/gravity-code/team/BEC
- Branch format: `sebadlf-bec-{n}-{descripcion}`

## Estado actual

- Single-module stateful client con globals para auth
- Sin tests, linter, ni formatter configurado
- Dependencias: `requests`, `python-dotenv`, `websocket-client`

## Decisiones

- [[ADR-001 — GET para todo]] — la API usa GET incluso para orders (no es un bug)

## Notas de dominio

- [[Conceptos Primary API]]
- [[Segmentos de mercado]]
