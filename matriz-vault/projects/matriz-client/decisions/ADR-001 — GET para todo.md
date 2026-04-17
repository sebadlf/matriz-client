---
date: 2026-04-16
status: accepted
tags: [adr, api-design]
---

# ADR-001: La API usa GET para todas las operaciones

## Contexto

La Primary API v1.21 de MATBA ROFEX usa HTTP GET para todas las operaciones, incluyendo envío de órdenes (`/rest/order/newSingleOrder`), cancelaciones, y modificaciones. Esto es contraintuitivo desde el punto de vista REST estándar.

## Decisión

Aceptamos el diseño tal cual está en la API. No intentamos "corregirlo" wrapeando en POST. El cliente usa GET para todo porque así funciona la API upstream.

## Consecuencias

- Los parámetros de órdenes van como query strings, no como body
- Cualquier reviewer que vea el código va a pensar que es un bug — documentar explícitamente en CLAUDE.md y en el código
- Logging de URLs puede exponer parámetros sensibles (cuidado con tokens en logs)
