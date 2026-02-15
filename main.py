from alpaca.trading.client import TradingClient
from config import get_alpaca_credentials


def main():
    """Test Alpaca API connection and display account info."""
    try:
        creds = get_alpaca_credentials()
        client = TradingClient(
            api_key=creds["api_key"],
            secret_key=creds["secret_key"],
            paper=creds["paper"],
        )

        account = client.get_account()

        print("Successfully connected to Alpaca!")
        print(f"Account ID: {account.id}")
        print(f"Account Status: {account.status}")
        print(f"Buying Power: ${float(account.buying_power):,.2f}")
        print(f"Portfolio Value: ${float(account.portfolio_value):,.2f}")
        print(f"Cash: ${float(account.cash):,.2f}")
        print(f"Paper Trading: {creds['paper']}")

    except ValueError as e:
        print(f"Configuration Error: {e}")
    except Exception as e:
        print(f"Error connecting to Alpaca: {e}")


if __name__ == "__main__":
    main()
