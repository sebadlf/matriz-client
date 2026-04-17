"""Pydantic models mirroring the TypedDicts in :mod:`matriz_client.types`.

Introduced in BEC-21 as a side-by-side alternative. The REST/WebSocket
clients still return TypedDicts at this stage; a follow-up ticket switches
them over.

Conventions:

* Field names stay in camelCase to match the wire format exactly. A later
  ticket may introduce snake_case aliases.
* ``ConfigDict(extra="ignore", populate_by_name=True, frozen=True)`` —
  tolerant to new fields from the API, immutable once constructed.
* Optional fields (i.e. those corresponding to ``total=False`` TypedDicts
  or ``NotRequired`` entries) default to ``None``.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from .types import (
    CFICode,
    Currency,
    MarketId,
    OrderStatus,
    OrderType,
    SegmentId,
    Side,
    TimeInForce,
)

__all__ = [
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
]


class _PrimaryModel(BaseModel):
    """Shared config for every Primary API response model."""

    model_config = ConfigDict(
        extra="ignore",
        populate_by_name=True,
        frozen=True,
    )


# ----------------------------------------------------------------------
# Identifiers
# ----------------------------------------------------------------------


class InstrumentId(_PrimaryModel):
    """Canonical identifier for an instrument (§5.1)."""

    marketId: MarketId
    symbol: str


class AccountId(_PrimaryModel):
    """Account wrapper used by WebSocket subscriptions (§7.1)."""

    id: str


# ----------------------------------------------------------------------
# Segments and instruments
# ----------------------------------------------------------------------


class Segment(_PrimaryModel):
    """Market segment descriptor (§4.1)."""

    marketSegmentId: SegmentId
    marketId: MarketId


class Instrument(_PrimaryModel):
    """Instrument header returned by list endpoints (§5.1)."""

    instrumentId: InstrumentId
    cficode: CFICode


class InstrumentDetail(_PrimaryModel):
    """Full instrument detail (§5.2).

    All fields are optional because the Primary API omits entries
    depending on the instrument's segment and CFI code (mirror of the
    ``TypedDict(total=False)`` in :mod:`matriz_client.types`).
    """

    instrumentId: InstrumentId | None = None
    cficode: CFICode | None = None
    segment: Segment | None = None
    lowLimitPrice: float | None = None
    highLimitPrice: float | None = None
    minPriceIncrement: float | None = None
    minTradeVol: float | None = None
    maxTradeVol: float | None = None
    tickSize: float | None = None
    contractMultiplier: float | None = None
    roundLot: float | None = None
    priceConvertionFactor: float | None = None
    maturityDate: str | None = None
    currency: Currency | None = None
    orderTypes: list[OrderType] | None = None
    timesInForce: list[TimeInForce] | None = None
    instrumentPricePrecision: int | None = None
    instrumentSizePrecision: int | None = None
    securityDescription: str | None = None
    tickPriceRanges: dict[str, Any] | None = None


# ----------------------------------------------------------------------
# Orders
# ----------------------------------------------------------------------


class NewOrderResponse(_PrimaryModel):
    """Identifiers returned by ``newSingleOrder`` / ``replaceById`` / ``cancelById`` (§6.3)."""

    clientId: str
    proprietary: str


class Order(_PrimaryModel):
    """Single order status record (§6.8).

    ``orderId`` is nullable because it is only assigned once the order is
    accepted by the exchange (§13).
    """

    orderId: str | None = None
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
    """Execution report (§7.5) — superset of :class:`Order`."""

    wsClOrdId: str | None = None


# ----------------------------------------------------------------------
# Market data
# ----------------------------------------------------------------------


class MarketDataLevel(_PrimaryModel):
    """Price level inside an order-book entry (``BI`` / ``OF``)."""

    price: float
    size: int


class MarketDataEntryValue(_PrimaryModel):
    """Scalar market-data entry (``LA``, ``SE``, ``OI`` …) per §8.1."""

    price: float | None = None
    size: int | None = None
    date: int | None = None


class MarketDataSnapshot(_PrimaryModel):
    """Market-data response (§8.1).

    Each key is optional; its presence matches the ``entries`` requested
    by the caller.
    """

    BI: list[MarketDataLevel] | None = None
    OF: list[MarketDataLevel] | None = None
    LA: MarketDataEntryValue | None = None
    SE: MarketDataEntryValue | None = None
    OI: MarketDataEntryValue | None = None
    OP: float | None = None
    CL: float | None = None
    HI: float | None = None
    LO: float | None = None
    TV: float | None = None
    IV: float | None = None
    EV: float | None = None
    NV: float | None = None
    ACP: float | None = None


class Trade(_PrimaryModel):
    """Historical trade record (§8.4)."""

    symbol: str
    servertime: int
    size: int
    price: float
    datetime: str


# ----------------------------------------------------------------------
# Risk API
# ----------------------------------------------------------------------


class Position(_PrimaryModel):
    """Aggregated position per symbol for an account (§9.1)."""

    symbol: str
    buySize: float
    buyPrice: float
    sellSize: float
    sellPrice: float
    totalDailyDiff: float
    totalDiff: float
    tradingSymbol: str


class DetailedPosition(_PrimaryModel):
    """Detailed position aggregated per account (§9.2)."""

    account: str | None = None
    totalDailyDiffPlain: float | None = None
    totalMarketValue: float | None = None
    report: dict[str, Any] | None = None
    lastCalculation: str | None = None


class AccountReport(_PrimaryModel):
    """Full account report with cash, margins and portfolio (§9.3)."""

    accountName: str | None = None
    marketMember: str | None = None
    marketMemberIdentity: str | None = None
    collateral: float | None = None
    margin: float | None = None
    availableToCollateral: float | None = None
    detailedAccountReports: dict[str, Any] | None = None
    portfolio: dict[str, Any] | None = None
    ordersMargin: float | None = None
    currentCash: float | None = None
    dailyDiff: float | None = None
    uncoveredMargin: float | None = None
