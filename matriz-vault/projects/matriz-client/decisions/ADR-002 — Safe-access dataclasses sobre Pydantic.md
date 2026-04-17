---
date: 2026-04-17
status: accepted
tags: [adr, api-design, types]
---

# ADR-002: Safe-access dataclasses como modelo de respuesta

## Contexto

La iteración inicial (BEC-21) introdujo modelos Pydantic para tipar las respuestas de la Primary API. Surgieron dos problemas:

- **Pydantic levanta `ValidationError` en runtime** si la API devuelve un tipo inesperado (p. ej. un string donde se esperaba un float). Eso interrumpe el flujo del cliente cuando lo único que el usuario quería era leer un par de campos.
- Los **TypedDicts** previos eran tipo solo en estático: en runtime son `dict` planos, así que `md["LA"]["price"]` lanza `KeyError` si la API omite `LA`. La Primary API omite entries con frecuencia (depende del segmento, hora del día, actividad).

Necesitamos un modelo donde el acceso encadenado (`snapshot.SE.price`) **nunca rompa**, aunque la wire payload sea parcial.

## Decisión

Reemplazar Pydantic por `@dataclass(frozen=True)` con un mixin `_SafeModel` que introspecciona type hints y construye instancias con defaults seguros:

- `list[X]` ausente → `[]`
- modelo anidado ausente → instancia vacía del modelo (todos sus atributos en default)
- escalar (`float`, `int`, `str`) ausente → `None`
- `dict[str, Any]` ausente → `{}`

Construcción vía `Model.from_api(payload)`; instancias frozen para desincentivar mutación de respuestas. Todas las funciones del REST y los frames del WS retornan estas clases.

## Alternativas consideradas

### Opción A: Pydantic con `model_validate` y try/except por endpoint
- Pro: validación real, errores tempranos.
- Contra: el usuario tiene que envolver cada llamada; inconsistente con la naturaleza "best-effort" de market data parcial.

### Opción B: TypedDicts + `.get()` en cascada
- Pro: cero runtime overhead.
- Contra: `md.get("LA", {}).get("price")` es ruidoso y se olvida en un call site cualquiera; tipos no expresan los defaults.

### Opción C: dataclasses + safe defaults (elegida)
- Pro: chaining seguro por construcción, frozen, atributos en lugar de subscript, sin dependencias extra.
- Contra: sin validación de tipos en runtime; campos extra de la API se ignoran silenciosamente.

## Consecuencias

- **Breaking change**: `0.1.x` (TypedDict / dict) → `0.2.0` (dataclasses). Documentado en `README.md` sección "Migrating from 0.1.x".
- Eliminamos `pydantic` del `dependencies`.
- `extra` keys del API se descartan silenciosamente (forward-compat OK, pero nuevas keys no aparecen hasta declararlas).
- Sin validación de tipos: si la API devuelve `price: "not a number"`, el modelo lo guarda como string. Detección queda en el lado del usuario / pruebas.
- `get_type_hints()` y `dataclass.fields()` se invocan por cada `from_api`. Si emerge como hot path (WS market data), cachear hints por clase.
- `UnknownFrame` no hereda de `_SafeModel`: preserva el dict crudo en `raw` para forward-compat de frames WS no modelados.

## Referencias

- Plan: `~/.claude/plans/foamy-hatching-cook.md`
- Tickets: BEC-26 (foundation), BEC-27 (REST), BEC-28 (cleanup), BEC-29 (WS), BEC-30 (release v0.2.0)
- Implementación: `matriz_client/models.py`
- [[Wire format y keys opcionales]] — el patrón del API que motivó el diseño
