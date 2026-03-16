from __future__ import annotations

import os
import time
from typing import Any

import requests as _requests
from dotenv import load_dotenv
from requests.auth import HTTPBasicAuth

from .exceptions import AuthenticationError, PrimaryAPIError

load_dotenv()

# -- Module-level state --
_base_url: str = os.getenv(
    "PRIMARY_BASE_URL", "https://api.remarkets.primary.com.ar"
).rstrip("/")
_user: str = os.getenv("PRIMARY_USER", "")
_password: str = os.getenv("PRIMARY_PASSWORD", "")
_token: str | None = None
_token_ts: float = 0.0
_TOKEN_TTL = 23 * 60 * 60  # refresh 1 h before the 24 h expiry
_session = _requests.Session()
_session.timeout = 30.0


# ------------------------------------------------------------------
# Auth
# ------------------------------------------------------------------


def _ensure_token() -> None:
    global _token, _token_ts
    if _token and (time.time() - _token_ts) < _TOKEN_TTL:
        return
    login()


def login() -> str:
    """Authenticate and store the token. Returns the token string."""
    global _token, _token_ts
    if not _user or not _password:
        raise AuthenticationError(
            "ERROR", "PRIMARY_USER and PRIMARY_PASSWORD must be set"
        )

    resp = _session.post(
        f"{_base_url}/auth/getToken",
        headers={"X-Username": _user, "X-Password": _password},
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
    url = f"{_base_url}{path}"
    if auth_basic:
        resp = _session.request(
            method, url, params=params, auth=HTTPBasicAuth(*auth_basic)
        )
    else:
        _ensure_token()
        assert _token is not None
        resp = _session.request(
            method, url, params=params, headers={"X-Auth-Token": _token}
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
    clean = {k: v for k, v in params.items() if v is not None}
    return _request("GET", path, params=clean)


def _risk_auth() -> tuple[str, str]:
    return (_user, _password)


# ------------------------------------------------------------------
# Segments  (§4)
# ------------------------------------------------------------------


def get_segments() -> list[dict[str, str]]:
    """Return all available market segments."""
    return _get("/rest/segment/all")["segments"]


# ------------------------------------------------------------------
# Instruments  (§5)
# ------------------------------------------------------------------


def get_all_instruments() -> list[dict[str, Any]]:
    """Return all instruments (basic info)."""
    return _get("/rest/instruments/all")["instruments"]


def get_instruments_details() -> list[dict[str, Any]]:
    """Return all instruments with full detail."""
    return _get("/rest/instruments/details")["instruments"]


def get_instrument_detail(symbol: str, market_id: str = "ROFX") -> dict[str, Any]:
    """Return detail for a single instrument."""
    return _get("/rest/instruments/detail", symbol=symbol, marketId=market_id)[
        "instrument"
    ]


def get_instruments_by_cfi(cfi_code: str) -> list[dict[str, Any]]:
    """Return instruments filtered by CFI code."""
    return _get("/rest/instruments/byCFICode", CFICode=cfi_code)["instruments"]


def get_instruments_by_segment(
    segment_id: str, market_id: str = "ROFX"
) -> list[dict[str, Any]]:
    """Return instruments in a given segment."""
    return _get(
        "/rest/instruments/bySegment", MarketSegmentID=segment_id, MarketID=market_id
    )["instruments"]


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
    """Submit a new order. Returns {"clientId": ..., "proprietary": ...}."""
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


def replace_order(
    cl_ord_id: str, proprietary: str, qty: int, price: float
) -> dict[str, Any]:
    """Replace (modify) an existing order by clOrdId."""
    return _get(
        "/rest/order/replaceById",
        clOrdId=cl_ord_id,
        proprietary=proprietary,
        orderQty=qty,
        price=price,
    )


def cancel_order(cl_ord_id: str, proprietary: str) -> dict[str, Any]:
    """Cancel an order by clOrdId."""
    return _get("/rest/order/cancelById", clOrdId=cl_ord_id, proprietary=proprietary)


def get_order_status(cl_ord_id: str, proprietary: str) -> dict[str, Any]:
    """Get the latest status of a request by clOrdId."""
    return _get("/rest/order/id", clOrdId=cl_ord_id, proprietary=proprietary)["order"]


def get_order_history(cl_ord_id: str, proprietary: str) -> dict[str, Any]:
    """Get all status transitions for a request by clOrdId."""
    return _get("/rest/order/allById", clOrdId=cl_ord_id, proprietary=proprietary)


def get_active_orders(account_id: str) -> dict[str, Any]:
    """Get all active orders for an account."""
    return _get("/rest/order/actives", accountId=account_id)


def get_filled_orders(account_id: str) -> dict[str, Any]:
    """Get all filled orders for an account."""
    return _get("/rest/order/filleds", accountId=account_id)


def get_all_orders(account_id: str) -> dict[str, Any]:
    """Get latest status of all requests for an account."""
    return _get("/rest/order/all", accountId=account_id)


def get_order_by_exec_id(exec_id: str) -> dict[str, Any]:
    """Get an order by its execution ID."""
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
    """Get real-time market data for an instrument."""
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
    """Get historical trades for an instrument."""
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
    """Get positions for an account (Risk API)."""
    return _request(
        "GET",
        f"/rest/risk/position/getPositions/{account_name}",
        auth_basic=_risk_auth(),
    )


def get_detailed_positions(account_name: str) -> dict[str, Any]:
    """Get detailed positions for an account (Risk API)."""
    return _request(
        "GET", f"/rest/risk/detailedPosition/{account_name}", auth_basic=_risk_auth()
    )


def get_account_report(account_name: str) -> dict[str, Any]:
    """Get account report (Risk API)."""
    return _request(
        "GET", f"/rest/risk/accountReport/{account_name}", auth_basic=_risk_auth()
    )
