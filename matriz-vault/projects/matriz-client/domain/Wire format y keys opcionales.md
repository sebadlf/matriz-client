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

## Cuidado: shape no obvio (ej. `CL` como objeto, no escalar)

Algunas keys que el sentido común sugiere como escalares vienen como sub-objetos `{price, size, date}`. Caso de referencia (issue [#102](https://github.com/sebadlf/matriz-client/issues/102), fix en `v0.2.1`):

- `OP` (Open) viene como **número plano**: `"OP": 180.35`.
- `CL` (Close) viene como **objeto**: `"CL": {"price": 180.35, "size": null, "date": 1669852800000}` — igual que `LA`/`SE`/`OI`.

La spec lo muestra así desde siempre (`primary_api_llm.md` §8.1, ejemplo de respuesta), pero el modelo declaraba `CL: float | None`, lo que rompía el safe-access (`md.CL` quedaba como `dict` crudo y `md.CL.price` levantaba `AttributeError`).

### Checklist al modelar una key nueva

1. **Mirar el ejemplo de respuesta de la spec** antes de elegir el tipo. Si la key aparece como objeto (`{price, size, date}` o cualquier otro), el tipo es un nested `_SafeModel`, no un escalar.
2. **Verificar contra runtime real** con un símbolo que tenga ese campo poblado. Para market data: símbolos con cierre del día anterior + último operado + ajuste son los más completos (ej. acciones líquidas en `MERV - XMEV - * - 24HS`).
3. **Cubrir el campo en el `from_spec_example` test** del modelo. Si el test no lo incluye, el bug pasa silencioso porque los nested models toleran ausencia.

### Pendiente de auditar

`HI`, `LO`, `IV`, `EV`, `NV`, `ACP` están declarados como `float | None` en `MarketDataSnapshot` pero no aparecen en el ejemplo de la spec. Antes de tocarlos hay que conseguir un payload real con esos campos para confirmar el shape.
