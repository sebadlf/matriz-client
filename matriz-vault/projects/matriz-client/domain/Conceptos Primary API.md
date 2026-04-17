---
tags: [domain, trading, primary-api]
---

# Conceptos clave de la Primary API

## Identificadores de órdenes

- **`clOrdId`** — identifica un *request* del cliente. Lo genera el cliente.
- **`orderId`** — identifica la *orden* en el exchange. Lo asigna MATBA ROFEX.
- Relación: un `clOrdId` puede resultar en un `orderId`, pero no siempre (si la orden es rechazada, no hay `orderId`).

## Autenticación

Dos modos:
1. **Token auth** — `POST /auth/getToken` devuelve un token. Se envía como header `X-Auth-Token`. Expira en ~24h.
2. **HTTP Basic Auth** — solo para Risk API. Usa usuario/contraseña directamente.

## Market Data Entries

| Código | Significado |
|--------|-------------|
| `BI` | Bid (mejor compra) |
| `OF` | Offer (mejor venta) |
| `LA` | Last (último precio operado) |
| `OP` | Open (apertura) |
| `CL` | Close (cierre) |
| `SE` | Settlement (precio de ajuste) |
| `OI` | Open Interest |
| `HI` | High (máximo del día) |
| `LO` | Low (mínimo del día) |
| `TV` | Trade Volume |
| `NV` | Nominal Volume |
| `EV` | Effective Volume |

## Tipos de orden

- `Limit` — precio límite
- `Market` — a mercado (mejor precio disponible)
- `Market_to_limit` — a mercado, pero se convierte en limit si no se ejecuta completa
- `Stop` — se activa cuando el precio alcanza un trigger

## Time in Force

- `DAY` — válida hasta fin de rueda
- `GTC` — Good Till Cancel
- `GTD` — Good Till Date
- `IOC` — Immediate Or Cancel
- `FOK` — Fill Or Kill
