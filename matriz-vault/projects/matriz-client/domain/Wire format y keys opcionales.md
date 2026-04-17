---
tags: [domain, api]
---

# Wire format y keys opcionales

La Primary API v1.21 omite keys con frecuencia en sus respuestas JSON, según segmento, hora del día, actividad del símbolo, o nivel de detalle del endpoint. **No es un bug**: es el contrato. El cliente debe asumir que cualquier key documentada puede no estar presente.

## Patrones observados

### Market Data (§8)

`GET /rest/marketdata/get?marketId=...&symbol=...&entries=BI,OF,LA,SE,OI,...` retorna un dict `marketData` donde cada entry pedida puede aparecer o no:

```json
{
  "marketData": {
    "BI": [{"price": 100.5, "size": 10}],
    "OF": [],
    "LA": {"price": 100.3, "size": 5, "date": 1681000000}
    // SE / OI / OP / CL / HI / LO ausentes si no hay actividad o el segmento no los soporta
  }
}
```

- Los entries de "book" (`BI`, `OF`) cuando ausentes pueden venir como `[]` o no venir directamente.
- Los entries escalares (`OP`, `CL`, `HI`, `LO`, `TV`) suelen omitirse si el símbolo no tradeó.
- Los entries con sub-objeto (`LA`, `SE`, `OI`) cuando ausentes simplemente no aparecen.

### Instrumentos (§5.2)

`InstrumentDetail` declara ~18 campos pero la API devuelve un subconjunto distinto por CFI/segmento (los productos sin maturity no traen `maturityDate`, los productos sin opciones no traen `tickPriceRanges`, etc.).

### Execution Reports (§7.5)

`OrderReport` evoluciona durante la vida de la orden: el primer reporte (`PENDING_NEW`) no trae `orderId` todavía; campos como `lastPx` / `lastQty` solo aparecen cuando hay un fill.

### Risk (§9)

`AccountReport.detailedAccountReports` y `portfolio` son dicts opaques cuya estructura depende del market member. Los tipamos como `dict[str, Any]`.

## Implicancia de diseño

Esto motivó [[ADR-002 — Safe-access dataclasses sobre Pydantic]]. El cliente nunca puede asumir que `payload["X"]` existe; el modelo lo absorbe con defaults.

## Cómo agregar un campo nuevo cuando el API lo expone

1. Declararlo en el `@dataclass` del modelo correspondiente (`matriz_client/models.py`) con su tipo y default seguro (`None` para escalar, `field(default_factory=list/dict)` para colecciones, `field(default_factory=NestedModel.empty)` para anidado).
2. No hace falta tocar `from_api` — el mixin lo descubre vía `get_type_hints`.
3. Test en `tests/test_models.py`: payload presente y payload sin la key.
