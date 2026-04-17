---
tags: [domain, trading, primary-api]
---

# Segmentos de mercado MATBA ROFEX

| Segmento | Nombre | Qué se opera |
|----------|--------|--------------|
| `DDF` | Derivados Financieros | Futuros y opciones sobre dólar, tasas, índices |
| `DDA` | Derivados Agrícolas | Futuros y opciones sobre soja, trigo, maíz, etc. |
| `DUAL` | Dual | Instrumentos que cotizan en ambos segmentos |
| `MERV` | Mercados Externos | Instrumentos de mercados conectados (ej: BYMA) |

## Formato de símbolos

Los instrumentos siguen un formato específico por segmento:

- Futuros de dólar: `DLR/[MES][AÑO]` — ej: `DLR/JUL26`
- Futuros de soja: `SOJ.ROS/[MES][AÑO]` — ej: `SOJ.ROS/MAY26`
- El sufijo `.ROS` indica entrega en Rosario

## Notas

- La lista completa de instrumentos se obtiene con `GET /rest/instruments/all`
- Los instrumentos tienen un `marketId` que corresponde al segmento
- Cada segmento tiene sus propias reglas de horario, tick size, y márgenes
