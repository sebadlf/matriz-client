"""Python client for the MATBA ROFEX Primary API v1.21.

Re-exports the REST (:mod:`.client`) and WebSocket (:mod:`.ws_client`)
surface as a flat namespace, so callers can simply do::

    import matriz_client as primary

    primary.login()
    segments = primary.get_segments()
    primary.ws_connect(on_message=my_handler)

See the README and the in-module docstrings for usage details.
"""

from .client import (
    cancel_order,
    get_account_report,
    get_active_orders,
    get_all_instruments,
    get_all_orders,
    get_detailed_positions,
    get_filled_orders,
    get_instrument_detail,
    get_instruments_by_cfi,
    get_instruments_by_segment,
    get_instruments_details,
    get_market_data,
    get_order_by_exec_id,
    get_order_history,
    get_order_status,
    get_positions,
    get_segments,
    get_trades,
    login,
    new_order,
    replace_order,
)
from .exceptions import AuthenticationError, PrimaryAPIError
from .types import (
    AccountId,
    AccountReport,
    CFICode,
    Currency,
    DetailedPosition,
    Instrument,
    InstrumentDetail,
    InstrumentId,
    MarketDataEntry,
    MarketDataEntryValue,
    MarketDataLevel,
    MarketDataSnapshot,
    MarketId,
    NewOrderResponse,
    Order,
    OrderReport,
    OrderStatus,
    OrderType,
    Position,
    Segment,
    SegmentId,
    Side,
    TimeInForce,
    Trade,
)
from .ws_client import (
    DEFAULT_MARKET_DATA_ENTRIES,
    MARKET_DATA_ENTRIES,
    ws_cancel_order,
    ws_connect,
    ws_disconnect,
    ws_is_connected,
    ws_new_order,
    ws_subscribe_market_data,
    ws_subscribe_order_reports,
)

__all__ = [
    "DEFAULT_MARKET_DATA_ENTRIES",
    "MARKET_DATA_ENTRIES",
    "AuthenticationError",
    "PrimaryAPIError",
    # REST
    "cancel_order",
    "get_account_report",
    "get_active_orders",
    "get_all_instruments",
    "get_all_orders",
    "get_detailed_positions",
    "get_filled_orders",
    "get_instrument_detail",
    "get_instruments_by_cfi",
    "get_instruments_by_segment",
    "get_instruments_details",
    "get_market_data",
    "get_order_by_exec_id",
    "get_order_history",
    "get_order_status",
    "get_positions",
    "get_segments",
    "get_trades",
    "login",
    "new_order",
    "replace_order",
    # Types — Literals
    "CFICode",
    "Currency",
    "MarketDataEntry",
    "MarketId",
    "OrderStatus",
    "OrderType",
    "SegmentId",
    "Side",
    "TimeInForce",
    # Types — TypedDicts
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
    # WebSocket
    "ws_cancel_order",
    "ws_connect",
    "ws_disconnect",
    "ws_is_connected",
    "ws_new_order",
    "ws_subscribe_market_data",
    "ws_subscribe_order_reports",
]
