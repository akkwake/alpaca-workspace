from alpaca.trading.client import TradingClient
from alpaca.trading.requests import CreateWatchlistRequest, UpdateWatchlistRequest
from config import get_alpaca_credentials


def get_trading_client():
    """Get authenticated trading client."""
    creds = get_alpaca_credentials()
    return TradingClient(
        api_key=creds["api_key"],
        secret_key=creds["secret_key"],
        paper=creds["paper"],
    )


def get_watchlists():
    """Get all watchlists."""
    client = get_trading_client()
    return client.get_watchlists()


def get_watchlist(watchlist_id: str):
    """Get a specific watchlist by ID."""
    client = get_trading_client()
    return client.get_watchlist_by_id(watchlist_id)


def get_watchlist_by_name(name: str):
    """Get a watchlist by name."""
    watchlists = get_watchlists()
    for wl in watchlists:
        if wl.name == name:
            return get_watchlist(str(wl.id))
    return None


def create_watchlist(name: str, symbols: list[str]):
    """Create a new watchlist."""
    client = get_trading_client()
    request = CreateWatchlistRequest(name=name, symbols=symbols)
    return client.create_watchlist(request)


def add_to_watchlist(watchlist_id: str, symbol: str):
    """Add a symbol to a watchlist."""
    client = get_trading_client()
    return client.add_asset_to_watchlist_by_id(watchlist_id, symbol)


def remove_from_watchlist(watchlist_id: str, symbol: str):
    """Remove a symbol from a watchlist."""
    client = get_trading_client()
    return client.remove_asset_from_watchlist_by_id(watchlist_id, symbol)


def update_watchlist(watchlist_id: str, name: str = None, symbols: list[str] = None):
    """Update a watchlist."""
    client = get_trading_client()
    request = UpdateWatchlistRequest(name=name, symbols=symbols)
    return client.update_watchlist_by_id(watchlist_id, request)


def delete_watchlist(watchlist_id: str):
    """Delete a watchlist."""
    client = get_trading_client()
    client.delete_watchlist_by_id(watchlist_id)


if __name__ == "__main__":
    print("=== Watchlist Management ===\n")

    # Get existing watchlists
    watchlists = get_watchlists()
    print(f"Existing watchlists: {len(watchlists)}")

    for wl in watchlists:
        print(f"\n  {wl.name} (ID: {wl.id})")
        full_wl = get_watchlist(str(wl.id))
        if full_wl.assets:
            for asset in full_wl.assets:
                print(f"    - {asset.symbol}")
        else:
            print("    (empty)")

    # Demo: Create a test watchlist if none exist
    if not watchlists:
        print("\nCreating demo watchlist 'Tech Giants'...")
        wl = create_watchlist("Tech Giants", ["AAPL", "GOOGL", "MSFT", "AMZN", "NVDA"])
        print(f"Created watchlist: {wl.name} with {len(wl.assets)} symbols")
