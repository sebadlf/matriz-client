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

    symbol = "MERV - XMEV - AL30 - 24HS"

    result = primary.new_order(symbol, "SELL", 50, ACCOUNT_1, price=91000)
    print(result)

    check = primary.get_order_status(result["clientId"], result["proprietary"])
    print(check)

    md = primary.get_market_data(symbol)
    print(f"Market data for {symbol}:", md)


if __name__ == "__main__":
    main()
