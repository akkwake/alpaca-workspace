from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetOrdersRequest
from alpaca.trading.enums import QueryOrderStatus
from config import get_alpaca_credentials


def get_trading_client():
    """Get authenticated trading client."""
    creds = get_alpaca_credentials()
    return TradingClient(
        api_key=creds["api_key"],
        secret_key=creds["secret_key"],
        paper=creds["paper"],
    )


def get_account_info():
    """Get account information."""
    client = get_trading_client()
    return client.get_account()


def get_positions():
    """Get all open positions."""
    client = get_trading_client()
    return client.get_all_positions()


def get_position(symbol: str):
    """Get position for a specific symbol."""
    client = get_trading_client()
    try:
        return client.get_open_position(symbol)
    except Exception:
        return None


def get_orders(status: str = "all", limit: int = 50):
    """Get orders with optional status filter."""
    client = get_trading_client()

    status_map = {
        "all": QueryOrderStatus.ALL,
        "open": QueryOrderStatus.OPEN,
        "closed": QueryOrderStatus.CLOSED,
    }

    request = GetOrdersRequest(
        status=status_map.get(status, QueryOrderStatus.ALL),
        limit=limit,
    )
    return client.get_orders(request)


def get_portfolio_history(period: str = "1M", timeframe: str = "1D"):
    """Get portfolio history."""
    client = get_trading_client()
    return client.get_portfolio_history(period=period, timeframe=timeframe)


def calculate_portfolio_stats():
    """Calculate portfolio statistics."""
    account = get_account_info()
    positions = get_positions()

    total_pl = sum(float(p.unrealized_pl) for p in positions)
    total_pl_pct = sum(float(p.unrealized_plpc) for p in positions) / len(positions) if positions else 0

    return {
        "portfolio_value": float(account.portfolio_value),
        "cash": float(account.cash),
        "buying_power": float(account.buying_power),
        "equity": float(account.equity),
        "total_positions": len(positions),
        "unrealized_pl": total_pl,
        "unrealized_pl_pct": total_pl_pct * 100,
    }


if __name__ == "__main__":
    print("=== Account Information ===\n")

    # Account info
    account = get_account_info()
    print(f"Account ID: {account.id}")
    print(f"Status: {account.status}")
    print(f"Portfolio Value: ${float(account.portfolio_value):,.2f}")
    print(f"Cash: ${float(account.cash):,.2f}")
    print(f"Buying Power: ${float(account.buying_power):,.2f}")
    print(f"Equity: ${float(account.equity):,.2f}")

    print("\n=== Positions ===\n")
    positions = get_positions()
    if positions:
        for pos in positions:
            pl = float(pos.unrealized_pl)
            pl_pct = float(pos.unrealized_plpc) * 100
            print(f"{pos.symbol}: {pos.qty} shares @ ${float(pos.avg_entry_price):.2f}")
            print(f"  Current: ${float(pos.current_price):.2f} | P&L: ${pl:+,.2f} ({pl_pct:+.2f}%)")
    else:
        print("No open positions")

    print("\n=== Recent Orders ===\n")
    orders = get_orders(limit=5)
    if orders:
        for order in orders:
            print(f"{order.symbol}: {order.side} {order.qty} @ {order.type} - {order.status}")
    else:
        print("No recent orders")

    print("\n=== Portfolio Stats ===\n")
    stats = calculate_portfolio_stats()
    for key, value in stats.items():
        if isinstance(value, float):
            print(f"{key}: ${value:,.2f}" if "pct" not in key else f"{key}: {value:.2f}%")
        else:
            print(f"{key}: {value}")
