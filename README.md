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
print(snapshot["BI"], snapshot["OF"])

resp = primary.new_order(
    symbol="DLR/DIC23",
    side="BUY",
    qty=10,
    account="REM6771",
    price=210.5,
)
print(resp["clientId"], resp["proprietary"])
```

## Quickstart — WebSocket

```python
import matriz_client as primary


def on_md(msg: dict) -> None:
    print("MD event:", msg)


primary.login()
primary.ws_connect(on_message=on_md)
primary.ws_subscribe_market_data(["DLR/DIC23"], depth=5)
```

## Typed API

`matriz_client` ships a `py.typed` marker (PEP 561) and exports `Literal` / `TypedDict` definitions for every enum-like parameter and JSON response. Import them from the flat namespace:

```python
from matriz_client import Side, OrderType, TimeInForce, Order, MarketDataSnapshot
```

## Reference

- Full Primary API v1.21 spec: [`primary_api_llm.md`](./primary_api_llm.md)
- Public surface: `matriz_client.__all__`

## License

MIT © Sebastián de la Fuente
