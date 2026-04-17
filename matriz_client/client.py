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
from typing import Any

import requests as _requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

from .exceptions import AuthenticationError, PrimaryAPIError
from .types import Segment

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


def get_all_instruments() -> list[dict[str, Any]]:
    """Return all tradable instruments with basic info (symbol + marketId)."""
    return _get("/rest/instruments/all")["instruments"]


def get_instruments_details() -> list[dict[str, Any]]:
    """Return all instruments with full detail (tick size, contract size, etc.)."""
    return _get("/rest/instruments/details")["instruments"]


def get_instrument_detail(symbol: str, market_id: str = "ROFX") -> dict[str, Any]:
    """Return the full detail record for a single instrument.

    Args:
        symbol: Instrument symbol (e.g. ``"DLR/DIC23"``).
        market_id: Market identifier; defaults to ``"ROFX"``.
    """
    return _get("/rest/instruments/detail", symbol=symbol, marketId=market_id)["instrument"]


def get_instruments_by_cfi(cfi_code: str) -> list[dict[str, Any]]:
    """Return instruments filtered by ISO 10962 CFI code (e.g. ``"FXXXSX"``)."""
    return _get("/rest/instruments/byCFICode", CFICode=cfi_code)["instruments"]


def get_instruments_by_segment(segment_id: str, market_id: str = "ROFX") -> list[dict[str, Any]]:
    """Return instruments belonging to the given market segment.

    Args:
        segment_id: One of ``"DDF"``, ``"DDA"``, ``"DUAL"``, ``"MERV"``.
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
    side: str,
    qty: int,
    account: str,
    price: float | None = None,
    *,
    order_type: str = "LIMIT",
    time_in_force: str = "DAY",
    market_id: str = "ROFX",
    cancel_previous: bool = False,
    iceberg: bool = False,
    display_qty: int | None = None,
    expire_date: str | None = None,
) -> dict[str, Any]:
    """Submit a new single order.

    Note: The Primary API accepts order submission over HTTP **GET**; this
    is a quirk of the upstream API, not a bug in this client.

    Args:
        symbol: Instrument symbol (e.g. ``"DLR/DIC23"``).
        side: ``"BUY"`` or ``"SELL"``.
        qty: Order quantity.
        account: Account ID to submit the order on behalf of.
        price: Limit price; required for ``order_type="LIMIT"``.
        order_type: ``"LIMIT"`` or ``"MARKET"``; defaults to ``"LIMIT"``.
        time_in_force: ``"DAY"``, ``"IOC"``, ``"FOK"`` or ``"GTD"``.
        market_id: Market identifier; defaults to ``"ROFX"``.
        cancel_previous: If ``True``, cancel previous active orders for the
            same instrument/account before placing this one.
        iceberg: Whether the order is iceberg (requires ``display_qty``).
        display_qty: Visible quantity for iceberg orders.
        expire_date: Expiry date for ``GTD`` orders (``"YYYYMMDD"``).

    Returns:
        Mapping with ``{"clientId": ..., "proprietary": ...}`` — together
        they identify the request in every subsequent call.
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


def replace_order(cl_ord_id: str, proprietary: str, qty: int, price: float) -> dict[str, Any]:
    """Modify an existing order, identified by ``(clOrdId, proprietary)``.

    Replacing an order atomically cancels the original and creates a new
    one with the same ``clOrdId`` but a new ``orderId`` at the exchange.
    """
    return _get(
        "/rest/order/replaceById",
        clOrdId=cl_ord_id,
        proprietary=proprietary,
        orderQty=qty,
        price=price,
    )


def cancel_order(cl_ord_id: str, proprietary: str) -> dict[str, Any]:
    """Cancel the order identified by ``(clOrdId, proprietary)``."""
    return _get("/rest/order/cancelById", clOrdId=cl_ord_id, proprietary=proprietary)


def get_order_status(cl_ord_id: str, proprietary: str) -> dict[str, Any]:
    """Return the latest status record for the request ``(clOrdId, proprietary)``."""
    return _get("/rest/order/id", clOrdId=cl_ord_id, proprietary=proprietary)["order"]


def get_order_history(cl_ord_id: str, proprietary: str) -> dict[str, Any]:
    """Return the full list of status transitions for ``(clOrdId, proprietary)``."""
    return _get("/rest/order/allById", clOrdId=cl_ord_id, proprietary=proprietary)


def get_active_orders(account_id: str) -> dict[str, Any]:
    """Return all orders currently active (``NEW`` or ``PARTIALLY_FILLED``) for an account."""
    return _get("/rest/order/actives", accountId=account_id)


def get_filled_orders(account_id: str) -> dict[str, Any]:
    """Return all fully filled orders for an account."""
    return _get("/rest/order/filleds", accountId=account_id)


def get_all_orders(account_id: str) -> dict[str, Any]:
    """Return the latest status record of every request sent by an account."""
    return _get("/rest/order/all", accountId=account_id)


def get_order_by_exec_id(exec_id: str) -> dict[str, Any]:
    """Return the order matching the given execution ID (``execId``)."""
    return _get("/rest/order/byExecId", execId=exec_id)


# ------------------------------------------------------------------
# Market Data  (§8)
# ------------------------------------------------------------------


def get_market_data(
    symbol: str,
    entries: str = "BI,OF,LA,OP,CL,SE,OI",
    *,
    market_id: str = "ROFX",
    depth: int | None = None,
) -> dict[str, Any]:
    """Return real-time market data for an instrument.

    Args:
        symbol: Instrument symbol (e.g. ``"DLR/DIC23"``).
        entries: Comma-separated list of entry codes:
            ``BI`` (bid), ``OF`` (offer), ``LA`` (last), ``OP`` (open),
            ``CL`` (close), ``SE`` (settlement), ``OI`` (open interest).
        market_id: Market identifier; defaults to ``"ROFX"``.
        depth: Book depth (1-5); ``None`` uses the server default.
    """
    return _get(
        "/rest/marketdata/get",
        marketId=market_id,
        symbol=symbol,
        entries=entries,
        depth=depth,
    )["marketData"]


def get_trades(
    symbol: str,
    *,
    date: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    market_id: str = "ROFX",
    environment: str | None = None,
) -> list[dict[str, Any]]:
    """Return historical trades for an instrument.

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


def get_positions(account_name: str) -> dict[str, Any]:
    """Return aggregated positions for an account (Risk API, HTTP Basic Auth)."""
    return _request(
        "GET",
        f"/rest/risk/position/getPositions/{account_name}",
        auth_basic=_risk_auth(),
    )


def get_detailed_positions(account_name: str) -> dict[str, Any]:
    """Return trade-level detailed positions for an account (Risk API)."""
    return _request("GET", f"/rest/risk/detailedPosition/{account_name}", auth_basic=_risk_auth())


def get_account_report(account_name: str) -> dict[str, Any]:
    """Return the full account report (cash, margins, P&L) for an account (Risk API)."""
    return _request("GET", f"/rest/risk/accountReport/{account_name}", auth_basic=_risk_auth())
