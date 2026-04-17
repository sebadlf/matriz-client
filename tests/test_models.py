"""Round-trip tests for :mod:`matriz_client.models` against spec payloads.

Payloads are hand-derived from the examples in ``primary_api_llm.md``. The
goal is to validate that the Pydantic models match the wire format and
that our ``extra="ignore"`` / ``frozen=True`` config behaves as expected.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from matriz_client.models import (
    AccountReport,
    DetailedPosition,
    Instrument,
    InstrumentDetail,
    InstrumentId,
    MarketDataEntryValue,
    MarketDataLevel,
    MarketDataSnapshot,
    NewOrderResponse,
    Order,
    OrderReport,
    Position,
    Segment,
    Trade,
)

# ----------------------------------------------------------------------
# Basic identifiers
# ----------------------------------------------------------------------


def test_instrument_id_round_trip() -> None:
    data = {"marketId": "ROFX", "symbol": "DLR/DIC23"}
    parsed = InstrumentId.model_validate(data)
    assert parsed.marketId == "ROFX"
    assert parsed.symbol == "DLR/DIC23"
    assert parsed.model_dump() == data


def test_segment_round_trip() -> None:
    data = {"marketSegmentId": "DDF", "marketId": "ROFX"}
    parsed = Segment.model_validate(data)
    assert parsed.marketSegmentId == "DDF"
    assert parsed.marketId == "ROFX"


def test_instrument_round_trip() -> None:
    data = {
        "instrumentId": {"marketId": "ROFX", "symbol": "DLR/DIC23"},
        "cficode": "FXXXSX",
    }
    parsed = Instrument.model_validate(data)
    assert parsed.instrumentId.symbol == "DLR/DIC23"
    assert parsed.cficode == "FXXXSX"


def test_instrument_detail_accepts_partial_payload() -> None:
    # InstrumentDetail is the Pydantic equivalent of TypedDict(total=False),
    # so an empty dict must parse successfully.
    detail = InstrumentDetail.model_validate({})
    assert detail.instrumentId is None
    assert detail.currency is None


# ----------------------------------------------------------------------
# Orders
# ----------------------------------------------------------------------


def test_new_order_response_round_trip() -> None:
    data = {"clientId": "1-1234", "proprietary": "PBCP"}
    parsed = NewOrderResponse.model_validate(data)
    assert parsed.clientId == "1-1234"
    assert parsed.proprietary == "PBCP"


ORDER_PAYLOAD = {
    "orderId": "218681",
    "clOrdId": "1-1234",
    "proprietary": "PBCP",
    "execId": "1669995044232",
    "accountId": "REM6771",
    "instrumentId": {"marketId": "ROFX", "symbol": "DLR/DIC23"},
    "price": 210.5,
    "orderQty": 10,
    "ordType": "LIMIT",
    "side": "BUY",
    "timeInForce": "DAY",
    "transactTime": "20230101-18:19:15.123-0300",
    "avgPx": 0.0,
    "lastPx": 0.0,
    "lastQty": 0,
    "cumQty": 0,
    "leavesQty": 10,
    "status": "NEW",
    "text": "",
}


def test_order_round_trip() -> None:
    parsed = Order.model_validate(ORDER_PAYLOAD)
    assert parsed.orderId == "218681"
    assert parsed.side == "BUY"
    assert parsed.instrumentId.symbol == "DLR/DIC23"


def test_order_accepts_null_order_id() -> None:
    # In pre-accept states (e.g. PENDING_NEW) the exchange returns orderId=null.
    payload = {**ORDER_PAYLOAD, "orderId": None, "status": "PENDING_NEW"}
    parsed = Order.model_validate(payload)
    assert parsed.orderId is None


def test_order_report_superset_of_order() -> None:
    report = OrderReport.model_validate({**ORDER_PAYLOAD, "wsClOrdId": "ws-abc"})
    assert report.wsClOrdId == "ws-abc"


# ----------------------------------------------------------------------
# Market data
# ----------------------------------------------------------------------


def test_market_data_level_round_trip() -> None:
    parsed = MarketDataLevel.model_validate({"price": 179.8, "size": 1000})
    assert parsed.price == 179.8
    assert parsed.size == 1000


def test_market_data_entry_value_allows_nulls() -> None:
    parsed = MarketDataEntryValue.model_validate(
        {"price": None, "size": 217596, "date": 1664150400000}
    )
    assert parsed.price is None
    assert parsed.size == 217596


def test_market_data_snapshot_from_spec_example() -> None:
    # Based on §8.1. ``CL`` in the live example is an object, but the
    # TypedDict declares it as a scalar — mirrored here. Tests use only
    # the fields that match the current type surface.
    payload = {
        "SE": {"price": 180.3, "size": None, "date": 1669852800000},
        "LA": {"price": 179.85, "size": 4, "date": 1669995044232},
        "OI": {"price": None, "size": 217596, "date": 1664150400000},
        "OF": [
            {"price": 179.8, "size": 1000},
            {"price": 180.35, "size": 1000},
        ],
        "OP": 180.35,
        "BI": [
            {"price": 179.75, "size": 275},
            {"price": 178.95, "size": 514},
        ],
    }
    parsed = MarketDataSnapshot.model_validate(payload)
    assert parsed.OP == 180.35
    assert parsed.BI is not None
    assert parsed.BI[0].price == 179.75
    assert parsed.SE is not None
    assert parsed.SE.size is None


def test_market_data_snapshot_accepts_empty_payload() -> None:
    parsed = MarketDataSnapshot.model_validate({})
    assert parsed.BI is None
    assert parsed.OP is None


# ----------------------------------------------------------------------
# Trades, Risk
# ----------------------------------------------------------------------


def test_trade_round_trip() -> None:
    parsed = Trade.model_validate(
        {
            "symbol": "DLR/DIC23",
            "servertime": 1669995044232,
            "size": 4,
            "price": 179.85,
            "datetime": "2022-12-02T18:20:44.232-03:00",
        }
    )
    assert parsed.price == 179.85


def test_position_round_trip() -> None:
    parsed = Position.model_validate(
        {
            "symbol": "DLR/DIC23",
            "buySize": 10.0,
            "buyPrice": 210.5,
            "sellSize": 0.0,
            "sellPrice": 0.0,
            "totalDailyDiff": 0.0,
            "totalDiff": 0.0,
            "tradingSymbol": "DLR/DIC23",
        }
    )
    assert parsed.symbol == "DLR/DIC23"


def test_detailed_position_accepts_partial_payload() -> None:
    parsed = DetailedPosition.model_validate({"account": "REM6771"})
    assert parsed.account == "REM6771"
    assert parsed.report is None


def test_account_report_accepts_partial_payload() -> None:
    parsed = AccountReport.model_validate(
        {"accountName": "REM6771", "collateral": 1000.0, "margin": 250.0}
    )
    assert parsed.accountName == "REM6771"
    assert parsed.portfolio is None


# ----------------------------------------------------------------------
# Config behavior
# ----------------------------------------------------------------------


def test_extra_fields_are_ignored() -> None:
    # Forward-compat: API can add fields without breaking the client.
    parsed = NewOrderResponse.model_validate(
        {"clientId": "1-1234", "proprietary": "PBCP", "newField": "future"}
    )
    assert parsed.clientId == "1-1234"
    assert not hasattr(parsed, "newField")


def test_models_are_frozen() -> None:
    parsed = NewOrderResponse.model_validate({"clientId": "1-1234", "proprietary": "PBCP"})
    with pytest.raises(ValidationError):
        parsed.clientId = "mutated"  # type: ignore[misc]


def test_missing_required_field_raises() -> None:
    with pytest.raises(ValidationError):
        NewOrderResponse.model_validate({"clientId": "only"})
