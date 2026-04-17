"""REST client for the MATBA ROFEX Primary API v1.21.

Thin wrapper over the HTTP endpoints of the Primary API. State is held at
module level (token, session, credentials) and the token is refreshed
automatically a little before the 24 h server-side expiry.

Auth modes:
- **Token** (default, most endpoints): obtained via ``POST /auth/getToken``
  and sent as ``X-Auth-Token`` on every subsequent request.
- **HTTP Basic** (Risk API only): uses ``PRIMARY_USER``/``PRIMARY_PASSWORD``
  directly on each request.

Environment variables (loaded from ``.env`` via ``python-dotenv``):
- ``PRIMARY_USER`` — API username (required)
- ``PRIMARY_PASSWORD`` — API password (required)
- ``PRIMARY_BASE_URL`` — defaults to ``https://api.remarkets.primary.com.ar``

See :mod:`matriz_client.ws_client` for the WebSocket streaming counterpart.
"""

from __future__ import annotations

import os
import time
from collections.abc import Sequence
from typing import Any, cast

import requests as _requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

from .exceptions import AuthenticationError, PrimaryAPIError
from .types import (
    DEFAULT_MARKET_DATA_ENTRIES,
    AccountReport,
    CFICode,
    DetailedPosition,
    Instrument,
    InstrumentDetail,
    MarketDataEntry,
    MarketDataSnapshot,
    MarketId,
    NewOrderResponse,
    Order,
    OrderType,
    Position,
    Segment,
    SegmentId,
    Side,
    TimeInForce,
    Trade,
)

load_dotenv()

# -- Module-level state --
_base_url: str = os.getenv("PRIMARY_BASE_URL", "https://api.remarkets.primary.com.ar").rstrip("/")
_user: str = os.getenv("PRIMARY_USER", "")
_password: str = os.getenv("PRIMARY_PASSWORD", "")
_token: str | None = None
_token_ts: float = 0.0
_TOKEN_TTL = 23 * 60 * 60  # refresh 1 h before the 24 h expiry
_session = _requests.Session()
_REQUEST_TIMEOUT = 30.0


# ------------------------------------------------------------------
# Auth
# ------------------------------------------------------------------


def _ensure_token() -> None:
    """Log in if there is no cached token or it is older than ``_TOKEN_TTL``."""
    global _token, _token_ts
    if _token and (time.time() - _token_ts) < _TOKEN_TTL:
        return
    login()


def login() -> str:
    """Authenticate against ``/auth/getToken`` and cache the resulting token.

    Returns:
        The newly issued token string, also stored in module state.

    Raises:
        AuthenticationError: If credentials are missing or the response has
            no ``X-Auth-Token`` header.
    """
    global _token, _token_ts
    if not _user or not _password:
        raise AuthenticationError("ERROR", "PRIMARY_USER and PRIMARY_PASSWORD must be set")

    resp = _session.post(
        f"{_base_url}/auth/getToken",
        headers={"X-Username": _user, "X-Password": _password},
        timeout=_REQUEST_TIMEOUT,
    )
    resp.raise_for_status()
    token = resp.headers.get("X-Auth-Token")
    if not token:
        raise AuthenticationError("ERROR", "No X-Auth-Token header in response")
    _token = token
    _token_ts = time.time()

    return token


# ------------------------------------------------------------------
# Internal helpers
# ------------------------------------------------------------------


def _request(
    method: str,
    path: str,
    *,
    params: dict[str, Any] | None = None,
    auth_basic: tuple[str, str] | None = None,
) -> dict[str, Any]:
    """Execute an HTTP request and decode the JSON payload.

    When ``auth_basic`` is provided, HTTP Basic Auth is used and the token
    flow is skipped (Risk API). Otherwise, the token is ensured/refreshed
    and sent via ``X-Auth-Token``.

    Raises:
        PrimaryAPIError: If the decoded payload has ``status == "ERROR"``.
    """
    url = f"{_base_url}{path}"
    if auth_basic:
        resp = _session.request(
            method,
            url,
            params=params,
            auth=HTTPBasicAuth(*auth_basic),
            timeout=_REQUEST_TIMEOUT,
        )
    else:
        _ensure_token()
        assert _token is not None
        resp = _session.request(
            method,
            url,
            params=params,
            headers={"X-Auth-Token": _token},
            timeout=_REQUEST_TIMEOUT,
        )

    resp.raise_for_status()
    data: dict[str, Any] = resp.json()
    if data.get("status") == "ERROR":
        raise PrimaryAPIError(
            status="ERROR",
            description=data.get("description"),
            message=data.get("message"),
        )
    return data


def _get(path: str, **params: Any) -> dict[str, Any]:
    """GET ``path`` with ``params`` after dropping keys whose value is ``None``."""
    clean = {k: v for k, v in params.items() if v is not None}
    return _request("GET", path, params=clean)


def _risk_auth() -> tuple[str, str]:
    """Return the (user, password) tuple used for Risk API HTTP Basic Auth."""
    return (_user, _password)


# ------------------------------------------------------------------
# Segments  (§4)
# ------------------------------------------------------------------


def get_segments() -> list[Segment]:
    """Return all available market segments.

    Each :class:`~matriz_client.types.Segment` carries its ``marketSegmentId``
    — one of ``DDF``, ``DDA``, ``DUAL``, ``MERV``, ``U-DDF``, ``U-DDA``,
    ``U-DUAL`` — and the owning ``marketId`` (§4).
    """
    return _get("/rest/segment/all")["segments"]


# ------------------------------------------------------------------
# Instruments  (§5)
# ------------------------------------------------------------------


def get_all_instruments() -> list[Instrument]:
    """Return all tradable instruments with basic info (symbol + ``marketId``)."""
    return _get("/rest/instruments/all")["instruments"]


def get_instruments_details() -> list[InstrumentDetail]:
    """Return all instruments with full detail (tick size, contract size, etc.)."""
    return _get("/rest/instruments/details")["instruments"]


def get_instrument_detail(symbol: str, market_id: MarketId = "ROFX") -> InstrumentDetail:
    """Return the full detail record for a single instrument.

    Args:
        symbol: Instrument symbol (e.g. ``"DLR/DIC23"``).
        market_id: Market identifier; defaults to ``"ROFX"`` (§12.1).
    """
    return _get("/rest/instruments/detail", symbol=symbol, marketId=market_id)["instrument"]


def get_instruments_by_cfi(cfi_code: CFICode) -> list[Instrument]:
    """Return instruments filtered by ISO 10962 CFI code.

    Accepted values (§5.4): ``ESXXXX``, ``DBXXXX``, ``OCASPS``, ``OPASPS``,
    ``FXXXSX``, ``OPAFXS``, ``OCAFXS``, ``EMXXXX``, ``DBXXFR``.
    """
    return _get("/rest/instruments/byCFICode", CFICode=cfi_code)["instruments"]


def get_instruments_by_segment(
    segment_id: SegmentId, market_id: MarketId = "ROFX"
) -> list[Instrument]:
    """Return instruments belonging to the given market segment.

    Args:
        segment_id: One of ``"DDF"``, ``"DDA"``, ``"DUAL"``, ``"MERV"``,
            ``"U-DDF"``, ``"U-DDA"``, ``"U-DUAL"`` (§5.5).
        market_id: Market identifier; defaults to ``"ROFX"``.
    """
    return _get("/rest/instruments/bySegment", MarketSegmentID=segment_id, MarketID=market_id)[
        "instruments"
    ]


# ------------------------------------------------------------------
# Orders  (§6)
# ------------------------------------------------------------------


def new_order(
    symbol: str,
    side: Side,
    qty: int,
    account: str,
    price: float | None = None,
    *,
    order_type: OrderType = "LIMIT",
    time_in_force: TimeInForce = "DAY",
    market_id: MarketId = "ROFX",
    cancel_previous: bool = False,
    iceberg: bool = False,
    display_qty: int | None = None,
    expire_date: str | None = None,
) -> NewOrderResponse:
    """Submit a new single order (§6.3).

    Note: The Primary API accepts order submission over HTTP **GET**; this
    is a quirk of the upstream API, not a bug in this client.

    Args:
        symbol: Instrument symbol (e.g. ``"DLR/DIC23"``).
        side: ``"BUY"`` or ``"SELL"`` (:data:`~matriz_client.types.Side`).
        qty: Order quantity.
        account: Account ID to submit the order on behalf of.
        price: Limit price; required for ``order_type="LIMIT"``.
        order_type: One of :data:`~matriz_client.types.OrderType`
            (``"LIMIT"``, ``"MARKET"``, ``"STOP_LIMIT"``,
            ``"STOP_LIMIT_MERVAL"``); defaults to ``"LIMIT"``.
        time_in_force: One of :data:`~matriz_client.types.TimeInForce`
            (``"DAY"``, ``"IOC"``, ``"FOK"``, ``"GTD"``).
        market_id: Market identifier; defaults to ``"ROFX"``.
        cancel_previous: If ``True``, cancel previous active orders for the
            same instrument/account before placing this one.
        iceberg: Whether the order is iceberg (requires ``display_qty``).
        display_qty: Visible quantity for iceberg orders.
        expire_date: Expiry date for ``GTD`` orders (``"YYYYMMDD"``).

    Returns:
        :class:`~matriz_client.types.NewOrderResponse` with ``clientId`` and
        ``proprietary`` — together they identify the request in every
        subsequent call.
    """
    params: dict[str, Any] = {
        "marketId": market_id,
        "symbol": symbol,
        "side": side,
        "orderQty": qty,
        "ordType": order_type,
        "timeInForce": time_in_force,
        "account": account,
        "cancelPrevious": str(cancel_previous),
        "iceberg": str(iceberg),
    }
    if price is not None:
        params["price"] = price
    if display_qty is not None:
        params["displayQty"] = display_qty
    if expire_date is not None:
        params["expireDate"] = expire_date

    return _get("/rest/order/newSingleOrder", **params)["order"]


def replace_order(cl_ord_id: str, proprietary: str, qty: int, price: float) -> NewOrderResponse:
    """Modify an existing order, identified by ``(clOrdId, proprietary)`` (§6.5).

    Replacing an order atomically cancels the original and creates a new
    one with the same ``clOrdId`` but a new ``orderId`` at the exchange.

    Returns:
        :class:`~matriz_client.types.NewOrderResponse` — the ``order``
        envelope unwrapped for consistency with :func:`new_order`.
    """
    return _get(
        "/rest/order/replaceById",
        clOrdId=cl_ord_id,
        proprietary=proprietary,
        orderQty=qty,
        price=price,
    )["order"]


def cancel_order(cl_ord_id: str, proprietary: str) -> NewOrderResponse:
    """Cancel the order identified by ``(clOrdId, proprietary)`` (§6.6).

    Returns:
        :class:`~matriz_client.types.NewOrderResponse` — the ``order``
        envelope unwrapped for consistency with :func:`new_order`.
    """
    return _get("/rest/order/cancelById", clOrdId=cl_ord_id, proprietary=proprietary)["order"]


def get_order_status(cl_ord_id: str, proprietary: str) -> Order:
    """Return the latest status record for the request ``(clOrdId, proprietary)`` (§6.8)."""
    return _get("/rest/order/id", clOrdId=cl_ord_id, proprietary=proprietary)["order"]


def get_order_history(cl_ord_id: str, proprietary: str) -> list[Order]:
    """Return the full list of status transitions for ``(clOrdId, proprietary)`` (§6.9).

    The ``orders`` envelope is unwrapped so callers iterate directly over
    :class:`~matriz_client.types.Order` records.
    """
    return _get("/rest/order/allById", clOrdId=cl_ord_id, proprietary=proprietary)["orders"]


def get_active_orders(account_id: str) -> list[Order]:
    """Return all orders currently active (``NEW`` or ``PARTIALLY_FILLED``) for an account (§6.10)."""
    return _get("/rest/order/actives", accountId=account_id)["orders"]


def get_filled_orders(account_id: str) -> list[Order]:
    """Return all fully filled orders for an account (§6.11)."""
    return _get("/rest/order/filleds", accountId=account_id)["orders"]


def get_all_orders(account_id: str) -> list[Order]:
    """Return the latest status record of every request sent by an account (§6.12)."""
    return _get("/rest/order/all", accountId=account_id)["orders"]


def get_order_by_exec_id(exec_id: str) -> Order:
    """Return the order matching the given execution ID (``execId``) (§6.13)."""
    return _get("/rest/order/byExecId", execId=exec_id)["order"]


# ------------------------------------------------------------------
# Market Data  (§8)
# ------------------------------------------------------------------


def get_market_data(
    symbol: str,
    entries: Sequence[MarketDataEntry] = DEFAULT_MARKET_DATA_ENTRIES,
    *,
    market_id: MarketId = "ROFX",
    depth: int | None = None,
) -> MarketDataSnapshot:
    """Return real-time market data for an instrument (§8.1).

    Args:
        symbol: Instrument symbol (e.g. ``"DLR/DIC23"``).
        entries: Sequence of entry codes — see
            :data:`~matriz_client.types.MARKET_DATA_ENTRIES` for the full
            catalogue. Defaults to
            :data:`~matriz_client.types.DEFAULT_MARKET_DATA_ENTRIES`.
        market_id: Market identifier; defaults to ``"ROFX"``.
        depth: Book depth (1-5); ``None`` uses the server default.
    """
    return _get(
        "/rest/marketdata/get",
        marketId=market_id,
        symbol=symbol,
        entries=",".join(entries),
        depth=depth,
    )["marketData"]


def get_trades(
    symbol: str,
    *,
    date: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    market_id: MarketId = "ROFX",
    environment: str | None = None,
) -> list[Trade]:
    """Return historical trades for an instrument (§8.4).

    Use ``date`` for a single day, or the ``date_from``/``date_to`` pair
    for a range. Dates must be in ``"YYYY-MM-DD"`` format.
    """
    return _get(
        "/rest/data/getTrades",
        marketId=market_id,
        symbol=symbol,
        date=date,
        dateFrom=date_from,
        dateTo=date_to,
        environment=environment,
    )["trades"]


# ------------------------------------------------------------------
# Risk API  (§9) — uses HTTP Basic Auth
# ------------------------------------------------------------------


def get_positions(account_name: str) -> list[Position]:
    """Return aggregated positions for an account (§9.1, HTTP Basic Auth).

    The ``positions`` envelope is unwrapped so callers iterate directly
    over :class:`~matriz_client.types.Position` records.
    """
    return _request(
        "GET",
        f"/rest/risk/position/getPositions/{account_name}",
        auth_basic=_risk_auth(),
    )["positions"]


def get_detailed_positions(account_name: str) -> DetailedPosition:
    """Return trade-level detailed positions for an account (§9.2).

    The Risk API returns the :class:`~matriz_client.types.DetailedPosition`
    fields at the top level (no ``status`` envelope), so the response is
    returned as-is.
    """
    return cast(
        DetailedPosition,
        _request("GET", f"/rest/risk/detailedPosition/{account_name}", auth_basic=_risk_auth()),
    )


def get_account_report(account_name: str) -> AccountReport:
    """Return the full account report (cash, margins, P&L) for an account (§9.3).

    As with :func:`get_detailed_positions`, the Risk API exposes the
    :class:`~matriz_client.types.AccountReport` fields at the top level.
    """
    return cast(
        AccountReport,
        _request("GET", f"/rest/risk/accountReport/{account_name}", auth_basic=_risk_auth()),
    )
