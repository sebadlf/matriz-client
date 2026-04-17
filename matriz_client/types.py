"""Shared type vocabulary for the Primary API v1.21 client.

Exports :class:`~typing.Literal` aliases for enum-like parameters
(``Side``, ``OrderType`` …) and :class:`~typing.TypedDict` definitions for
the JSON payloads produced by the Primary API. Consumers — including
:mod:`matriz_client.client` — should import their types from here so there
is a single source of truth derived from ``primary_api_llm.md`` v1.21.

Conventions:

* ``TypedDict`` rather than ``dataclass`` — responses are plain ``dict``
  objects coming out of ``json.loads``.
* Required fields live in ``total=True`` classes; truly optional fields use
  :data:`typing.NotRequired`. For responses where the Primary API omits
  fields by segment/CFI (e.g. :class:`InstrumentDetail`), the dict uses
  ``total=False`` and documents the always-present backbone in its
  docstring.
* Nested structures that the spec leaves open-ended (``tickPriceRanges``,
  ``report``, ``portfolio``, ``detailedAccountReports``) are typed as
  ``dict[str, Any]`` until the shape is nailed down.
"""

from __future__ import annotations

from typing import Any, Literal, NotRequired, TypedDict

__all__ = [
    # Literals
    "CFICode",
    "Currency",
    "MarketDataEntry",
    "MarketId",
    "OrderStatus",
    "OrderType",
    "SegmentId",
    "Side",
    "TimeInForce",
    # TypedDicts
    "AccountId",
    "AccountReport",
    "DetailedPosition",
    "Instrument",
    "InstrumentDetail",
    "InstrumentId",
    "MarketDataEntryValue",
    "MarketDataLevel",
    "MarketDataSnapshot",
    "NewOrderResponse",
    "Order",
    "OrderReport",
    "Position",
    "Segment",
    "Trade",
    # Constants
    "DEFAULT_MARKET_DATA_ENTRIES",
    "MARKET_DATA_ENTRIES",
]


# ----------------------------------------------------------------------
# Literals
# ----------------------------------------------------------------------

Side = Literal["BUY", "SELL"]
"""Order side (§6.3, §12.5)."""

OrderType = Literal["LIMIT", "MARKET", "STOP_LIMIT", "STOP_LIMIT_MERVAL"]
"""Order type (§12.5)."""

TimeInForce = Literal["DAY", "IOC", "FOK", "GTD"]
"""Order time-in-force (§6.3)."""

MarketId = Literal["ROFX"]
"""Market identifier (§12.1 — ``ROFX`` is the only documented value)."""

SegmentId = Literal["DDF", "DDA", "DUAL", "MERV", "U-DDF", "U-DDA", "U-DUAL"]
"""Market segment identifier (§5.5)."""

CFICode = Literal[
    "ESXXXX",
    "DBXXXX",
    "OCASPS",
    "OPASPS",
    "FXXXSX",
    "OPAFXS",
    "OCAFXS",
    "EMXXXX",
    "DBXXFR",
]
"""ISO 10962 CFI code accepted by ``/rest/instruments/byCFICode`` (§5.4)."""

MarketDataEntry = Literal[
    "BI",
    "OF",
    "LA",
    "OP",
    "CL",
    "SE",
    "HI",
    "LO",
    "TV",
    "OI",
    "IV",
    "EV",
    "NV",
    "ACP",
]
"""Market-data entry code (§8.3)."""

OrderStatus = Literal[
    "NEW",
    "PENDING_NEW",
    "PENDING_REPLACE",
    "PENDING_CANCEL",
    "REJECTED",
    "PENDING_APPROVAL",
    "CANCELLED",
    "REPLACED",
    "FILLED",
    "PARTIALLY_FILLED",
]
"""Order life-cycle status (§11)."""

Currency = Literal["ARS", "USD"]
"""Currency observed in instrument detail responses."""


# ----------------------------------------------------------------------
# Market-data entry catalogues (§8.3)
# ----------------------------------------------------------------------

MARKET_DATA_ENTRIES: tuple[MarketDataEntry, ...] = (
    "BI",  # best bid
    "OF",  # best offer
    "LA",  # last traded price
    "OP",  # open price
    "CL",  # previous close
    "SE",  # settlement
    "HI",  # session high
    "LO",  # session low
    "TV",  # traded volume
    "OI",  # open interest
    "IV",  # index value
    "EV",  # effective volume (ByMA)
    "NV",  # nominal volume (ByMA)
    "ACP",  # today's close
)
"""Full catalogue of market-data entry codes recognised by the Primary API."""

DEFAULT_MARKET_DATA_ENTRIES: tuple[MarketDataEntry, ...] = (
    "BI",
    "OF",
    "LA",
    "OP",
    "CL",
    "SE",
    "OI",
)
"""Default subset used when the caller does not specify ``entries``."""


# ----------------------------------------------------------------------
# TypedDicts
# ----------------------------------------------------------------------


class InstrumentId(TypedDict):
    """Canonical identifier for an instrument (§5.1)."""

    marketId: MarketId
    symbol: str


class AccountId(TypedDict):
    """Account wrapper used by WebSocket subscriptions (§7.1)."""

    id: str


class Segment(TypedDict):
    """Market segment descriptor (§4.1)."""

    marketSegmentId: SegmentId
    marketId: MarketId


class Instrument(TypedDict):
    """Instrument header returned by list endpoints (§5.1)."""

    instrumentId: InstrumentId
    cficode: CFICode


class InstrumentDetail(TypedDict, total=False):
    """Full instrument detail (§5.2).

    Marked ``total=False`` because the Primary API omits a number of
    fields depending on the instrument's segment and CFI code. In
    practice ``instrumentId``, ``cficode`` and ``segment`` are always
    populated.
    """

    instrumentId: InstrumentId
    cficode: CFICode
    segment: Segment
    lowLimitPrice: float
    highLimitPrice: float
    minPriceIncrement: float
    minTradeVol: float
    maxTradeVol: float
    tickSize: float
    contractMultiplier: float
    roundLot: float
    priceConvertionFactor: float
    maturityDate: str
    currency: Currency
    orderTypes: list[OrderType]
    timesInForce: list[TimeInForce]
    instrumentPricePrecision: int
    instrumentSizePrecision: int
    securityDescription: str
    tickPriceRanges: dict[str, Any]


class NewOrderResponse(TypedDict):
    """Identifiers returned by ``newSingleOrder`` / ``replaceById`` / ``cancelById`` (§6.3)."""

    clientId: str
    proprietary: str


class Order(TypedDict):
    """Single order status record (§6.8).

    ``orderId`` is nullable because it is only assigned once the order is
    accepted by the exchange — prior states (e.g. ``PENDING_NEW``) report
    ``null`` (§13).
    """

    orderId: str | None
    clOrdId: str
    proprietary: str
    execId: str
    accountId: str
    instrumentId: InstrumentId
    price: float
    orderQty: float
    ordType: OrderType
    side: Side
    timeInForce: TimeInForce
    transactTime: str
    avgPx: float
    lastPx: float
    lastQty: float
    cumQty: float
    leavesQty: float
    status: OrderStatus
    text: str


class OrderReport(Order):
    """Execution report (§7.5) — superset of :class:`Order`.

    ``wsClOrdId`` is only present when the originating order was sent over
    WebSocket with a client-assigned identifier.
    """

    wsClOrdId: NotRequired[str]


class MarketDataLevel(TypedDict):
    """Price level inside an order-book entry (``BI`` / ``OF``)."""

    price: float
    size: int


class MarketDataEntryValue(TypedDict, total=False):
    """Scalar market-data entry (``LA``, ``SE``, ``OI`` …) per §8.1.

    All fields are optional because the server omits missing values.
    """

    price: float | None
    size: int | None
    date: int | None


class MarketDataSnapshot(TypedDict, total=False):
    """Market-data response (§8.1).

    Each key is optional; its presence matches the ``entries`` requested
    via :func:`matriz_client.client.get_market_data`. Value shape depends
    on the entry:

    * ``BI``, ``OF`` — book depth as ``list[MarketDataLevel]``
    * ``LA``, ``SE``, ``OI`` — scalar entries as :class:`MarketDataEntryValue`
    * ``OP``, ``CL``, ``HI``, ``LO``, ``TV``, ``IV``, ``EV``, ``NV``, ``ACP`` — plain ``float``
    """

    BI: list[MarketDataLevel]
    OF: list[MarketDataLevel]
    LA: MarketDataEntryValue
    SE: MarketDataEntryValue
    OI: MarketDataEntryValue
    OP: float
    CL: float
    HI: float
    LO: float
    TV: float
    IV: float
    EV: float
    NV: float
    ACP: float


class Trade(TypedDict):
    """Historical trade record (§8.4)."""

    symbol: str
    servertime: int
    size: int
    price: float
    datetime: str


class Position(TypedDict):
    """Aggregated position per symbol for an account (§9.1)."""

    symbol: str
    buySize: float
    buyPrice: float
    sellSize: float
    sellPrice: float
    totalDailyDiff: float
    totalDiff: float
    tradingSymbol: str


class DetailedPosition(TypedDict, total=False):
    """Detailed position aggregated per account (§9.2)."""

    account: str
    totalDailyDiffPlain: float
    totalMarketValue: float
    report: dict[str, Any]
    lastCalculation: str


class AccountReport(TypedDict, total=False):
    """Full account report with cash, margins and portfolio (§9.3)."""

    accountName: str
    marketMember: str
    marketMemberIdentity: str
    collateral: float
    margin: float
    availableToCollateral: float
    detailedAccountReports: dict[str, Any]
    portfolio: dict[str, Any]
    ordersMargin: float
    currentCash: float
    dailyDiff: float
    uncoveredMargin: float
