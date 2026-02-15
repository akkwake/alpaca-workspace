from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetAssetsRequest
from alpaca.trading.enums import AssetClass, AssetStatus
from config import get_alpaca_credentials


def get_trading_client():
    """Get authenticated trading client."""
    creds = get_alpaca_credentials()
    return TradingClient(
        api_key=creds["api_key"],
        secret_key=creds["secret_key"],
        paper=creds["paper"],
    )


def get_asset(symbol: str):
    """Get asset details by symbol."""
    client = get_trading_client()
    try:
        return client.get_asset(symbol)
    except Exception:
        return None


def search_assets(
    status: str = "active",
    asset_class: str = "us_equity",
    exchange: str = None,
):
    """Search for assets with filters."""
    client = get_trading_client()

    status_map = {
        "active": AssetStatus.ACTIVE,
        "inactive": AssetStatus.INACTIVE,
    }

    class_map = {
        "us_equity": AssetClass.US_EQUITY,
        "crypto": AssetClass.CRYPTO,
    }

    request = GetAssetsRequest(
        status=status_map.get(status, AssetStatus.ACTIVE),
        asset_class=class_map.get(asset_class, AssetClass.US_EQUITY),
        exchange=exchange,
    )
    return client.get_all_assets(request)


def find_tradeable_stocks(search_term: str = None, limit: int = 20):
    """Find tradeable stocks, optionally filtering by search term."""
    assets = search_assets(status="active", asset_class="us_equity")

    tradeable = [
        a for a in assets
        if a.tradable and a.fractionable
    ]

    if search_term:
        search_upper = search_term.upper()
        tradeable = [
            a for a in tradeable
            if search_upper in a.symbol or search_upper in (a.name or "").upper()
        ]

    return tradeable[:limit]


def get_crypto_assets():
    """Get all available crypto assets."""
    assets = search_assets(status="active", asset_class="crypto")
    return [a for a in assets if a.tradable]


if __name__ == "__main__":
    print("=== Asset Search ===\n")

    # Get specific asset
    print("Looking up AAPL...")
    asset = get_asset("AAPL")
    if asset:
        print(f"  Symbol: {asset.symbol}")
        print(f"  Name: {asset.name}")
        print(f"  Exchange: {asset.exchange}")
        print(f"  Tradable: {asset.tradable}")
        print(f"  Fractionable: {asset.fractionable}")
        print(f"  Shortable: {asset.shortable}")

    # Search for stocks
    print("\n--- Searching for 'tech' stocks ---")
    tech_stocks = find_tradeable_stocks("tech", limit=10)
    for stock in tech_stocks:
        print(f"  {stock.symbol}: {stock.name}")

    # Search for AI-related stocks
    print("\n--- Searching for 'AI' stocks ---")
    ai_stocks = find_tradeable_stocks("AI", limit=10)
    for stock in ai_stocks:
        print(f"  {stock.symbol}: {stock.name}")

    # Crypto assets
    print("\n--- Available Crypto ---")
    crypto = get_crypto_assets()
    print(f"  {len(crypto)} crypto assets available")
    for c in crypto[:10]:
        print(f"  {c.symbol}: {c.name}")
