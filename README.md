# matriz-client

Python client for the [MATBA ROFEX Primary API v1.21](./primary_api_llm.md) — a REST + WebSocket API for electronic trading on Argentina's derivatives and securities exchange. The library wraps every public endpoint (segments, instruments, orders, market data, risk) into typed Python functions with automatic token management.

Requires Python 3.12+.

## Installation

Install from a built wheel (GitHub Releases):

```bash
pip install https://github.com/sebadlf/matriz-client/releases/download/<VERSION>/matriz_client-<VERSION>-py3-none-any.whl
```

Or clone and install from source:

```bash
git clone https://github.com/sebadlf/matriz-client.git
cd matriz-client
uv sync
```

## Configuration

The client loads credentials from environment variables (or a `.env` file via `python-dotenv`):

| Variable | Description |
|---|---|
| `PRIMARY_USER` | API username (required) |
| `PRIMARY_PASSWORD` | API password (required) |
| `PRIMARY_BASE_URL` | REST base URL. Defaults to `https://api.remarkets.primary.com.ar` (reMarkets sandbox). |

## Quickstart — REST

```python
import matriz_client as primary

primary.login()

segments = primary.get_segments()
instruments = primary.get_instruments_by_segment("DDF")

snapshot = primary.get_market_data("DLR/DIC23", depth=5)
print(snapshot.BI, snapshot.OF)

resp = primary.new_order(
    symbol="DLR/DIC23",
    side="BUY",
    qty=10,
    account="REM6771",
    price=210.5,
)
print(resp.clientId, resp.proprietary)
```

## Quickstart — WebSocket

```python
import matriz_client as primary
from matriz_client import (
    ExecutionReportFrame,
    MarketDataFrame,
    PrimaryWsMessage,
    UnknownFrame,
)


def on_msg(msg: PrimaryWsMessage) -> None:
    if isinstance(msg, MarketDataFrame):
        print(msg.instrumentId.symbol, msg.marketData.BI, msg.marketData.OF)
    elif isinstance(msg, ExecutionReportFrame):
        print(msg.orderReport.clOrdId, msg.orderReport.status)
    elif isinstance(msg, UnknownFrame):
        print("unhandled frame:", msg.type, msg.raw)


primary.login()
primary.ws_connect(on_message=on_msg)
primary.ws_subscribe_market_data(["DLR/DIC23"], depth=5)
```

## Typed API

`matriz_client` ships a `py.typed` marker (PEP 561) and exports `Literal` aliases plus safe-access dataclasses for every enum-like parameter and JSON response. Missing keys collapse to safe defaults so chained access (e.g. `snapshot.SE.price`) never raises. Import them from the flat namespace:

```python
from matriz_client import Side, OrderType, TimeInForce, Order, MarketDataSnapshot
```

## Migrating from 0.1.x

`0.2.0` replaces dict-based responses (TypedDicts) with frozen safe-access dataclasses. Field access is by attribute, not subscript:

```python
# 0.1.x — TypedDict / raw JSON
md = primary.get_market_data("DLR/DIC23")
print(md["OP"], md["BI"][0]["price"])     # KeyError if "OP" or "BI" missing

resp = primary.new_order(...)
print(resp["clientId"])

# 0.2.0 — safe-access dataclasses
md = primary.get_market_data("DLR/DIC23")
print(md.OP, md.BI[0].price)              # md.OP can be None, never raises
print(md.SE.price)                        # nested chain safe even if "SE" missing

resp = primary.new_order(...)
print(resp.clientId)
```

WebSocket callbacks now receive a tagged `PrimaryWsMessage` instead of a raw `dict`:

```python
# 0.1.x
def on_msg(msg: dict) -> None:
    if msg["type"] == "Md":
        print(msg["marketData"]["BI"])

# 0.2.0
def on_msg(msg: PrimaryWsMessage) -> None:
    if isinstance(msg, MarketDataFrame):
        print(msg.marketData.BI)
```

**Safety guarantee.** Missing keys never raise `KeyError`/`AttributeError`. Lists default to `[]`, nested models to an empty instance, scalars to `None`, dicts to `{}`. Chained access like `snapshot.SE.price` always resolves — the worst case is a final `None`.

## Reference

- Full Primary API v1.21 spec: [`primary_api_llm.md`](./primary_api_llm.md)
- Public surface: `matriz_client.__all__`

## Releases

Distribution happens via GitHub Releases (no PyPI). The [`release.yml`](.github/workflows/release.yml) workflow builds and publishes a wheel + sdist on every `v*` tag push.

Cutting a new release:

1. Bump `project.version` in `pyproject.toml`.
2. Commit and merge the bump to `main`.
3. Tag the commit: `git tag v0.1.0 && git push origin v0.1.0`.
4. The workflow validates that the tag matches the version, builds the artifacts, and uploads them to the corresponding Release.

## License

MIT © Sebastián de la Fuente
