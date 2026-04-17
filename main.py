"""Example usage of the Primary API client.

Requires a .env file with PRIMARY_USER and PRIMARY_PASSWORD.
"""

import matriz_client as primary

# usuario: api_bbsa
# contraseña: ktMqm7sD_

ACCOUNT_1 = "xprimary"
ACCOUNT_2 = "99998"


def main() -> None:

    # segments = primary.get_segments()
    # # print("Segments:", segments)

    # instruments = primary.get_instruments_by_segment("MERV")
    # # print(f"DDF instruments: {len(instruments)}")

    # if instruments:
    #     # symbol = instruments[0]["symbol"]
    #     symbol = "MERV - XMEV - AL30 - 24HS"
    #     md = primary.get_market_data(symbol)
    #     print(f"Market data for {symbol}:", md)

    # # Orders and Risk require an explicit account
    # active = primary.get_active_orders("REM6771")
    # print("Active orders:", active)

    # report = primary.get_account_report("REM6771")
    # print("Account report:", report)

    symbol = "MERV - XMEV - AAPL - 24HS"

    print(primary.get_market_data(symbol, depth=5))

    # result = primary.new_order(symbol, "SELL", 1, "5208", None, order_type="MARKET")
    # print(result)
    # print("")

    # time.sleep(3)

    # check = primary.get_order_status(result["clientId"], result["proprietary"])
    # print(check)
    # print("")

    # time.sleep(3)

    # check = primary.get_order_status(result["clientId"], result["proprietary"])
    # print(check)
    # print("")

    # time.sleep(3)

    # check = primary.get_order_status(result["clientId"], result["proprietary"])
    # print(check)
    # print("")

    # md = primary.get_market_data(symbol)
    # print(f"Market data for {symbol}:", md)
    # print("")

    # check = primary.get_order_status(result["clientId"], result["proprietary"])
    # print(check)
    # print("")

    # md = primary.get_market_data(symbol)
    # print(f"Market data for {symbol}:", md)
    # print("")

    # check = primary.get_order_status("512599370000059", "ISV_PBCP")
    # print(check)
    # print("")


if __name__ == "__main__":
    main()
