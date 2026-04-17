"""Example usage of the Primary API WebSocket client.

Requires a .env file with PRIMARY_USER and PRIMARY_PASSWORD.

Connects via WebSocket, subscribes to market data and execution reports,
then sends an order and waits for messages.
"""

import signal
import time

import matriz_client as primary
from main import ACCOUNT_1

ACCOUNT = "xprimary"
SYMBOL = "MERV - XMEV - AL30 - 24HS"

_running = True


def on_message(msg: dict) -> None:
    msg_type = msg.get("type", "unknown")

    if msg_type == "Md":
        instrument = msg["instrumentId"]["symbol"]
        md = msg["marketData"]
        print(f"[MarketData] {instrument}: {md}")

    elif msg_type == "or":
        report = msg["orderReport"]
        status = report.get("status")
        symbol = report["instrumentId"]["symbol"]
        cl_ord_id = report.get("clOrdId")
        text = report.get("text", "")
        print(f"[OrderReport] {symbol} | status={status} clOrdId={cl_ord_id} | {text}")

    else:
        print(f"[{msg_type}] {msg}")


def on_error(error: Exception) -> None:
    print(f"[Error] {error}")


def on_close() -> None:
    global _running
    print("[Closed] WebSocket connection closed")
    _running = False


def stop(signum: int, frame: object) -> None:
    global _running
    print("\nShutting down...")
    _running = False


def main() -> None:
    signal.signal(signal.SIGINT, stop)

    # 1. Connect
    print("Connecting to WebSocket...")
    primary.ws_connect(
        on_message=on_message,
        on_error=on_error,
        on_close=on_close,
    )
    print("Connected!")

    # # 2. Subscribe to execution reports for our account
    # print(f"Subscribing to execution reports for {ACCOUNT}...")
    # primary.ws_subscribe_order_reports(account=ACCOUNT)

    # 3. Subscribe to market data
    print(f"Subscribing to market data for {SYMBOL}...")
    primary.ws_subscribe_market_data(
        symbols=[SYMBOL],
        # entries=["BI", "OF", "LA"],
        depth=1,
    )

    result = primary.new_order(SYMBOL, "SELL", 2, ACCOUNT_1, price=91000)
    print(result)

    check = primary.get_order_status(result["clientId"], result["proprietary"])
    print(check)
    print("")

    md = primary.get_market_data(SYMBOL)
    print(f"Market data for {SYMBOL}:", md)
    print("")

    # # 4. Send an order
    # print(f"Sending order: SELL 50 {SYMBOL} @ 91000...")
    # primary.ws_new_order(
    #     symbol=SYMBOL,
    #     side="BUY",
    #     quantity=5,
    #     account=ACCOUNT,
    #     price=90200,
    #     ws_cl_ord_id="example-ws-order-2",
    # )

    # 5. Keep running until Ctrl+C
    print("\nListening for messages (Ctrl+C to quit)...\n")
    while _running:
        time.sleep(0.5)

    primary.ws_disconnect()
    print("Done.")


if __name__ == "__main__":
    main()
