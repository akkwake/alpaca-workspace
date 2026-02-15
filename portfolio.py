from datetime import datetime, timedelta
from alpaca.trading.client import TradingClient
from alpaca.trading.requests import GetPortfolioHistoryRequest
from config import get_alpaca_credentials


def get_trading_client():
    """Get authenticated trading client."""
    creds = get_alpaca_credentials()
    return TradingClient(
        api_key=creds["api_key"],
        secret_key=creds["secret_key"],
        paper=creds["paper"],
    )


def get_account_snapshot():
    """Get current account snapshot."""
    client = get_trading_client()
    account = client.get_account()

    return {
        "timestamp": datetime.now().isoformat(),
        "portfolio_value": float(account.portfolio_value),
        "cash": float(account.cash),
        "buying_power": float(account.buying_power),
        "equity": float(account.equity),
        "long_market_value": float(account.long_market_value),
        "short_market_value": float(account.short_market_value),
        "initial_margin": float(account.initial_margin),
        "maintenance_margin": float(account.maintenance_margin),
        "last_equity": float(account.last_equity),
        "daytrade_count": account.daytrade_count,
        "pattern_day_trader": account.pattern_day_trader,
    }


def get_portfolio_history(period: str = "1M", timeframe: str = "1D", extended_hours: bool = False):
    """
    Get portfolio history.

    Args:
        period: 1D, 1W, 1M, 3M, 6M, 1A, all
        timeframe: 1Min, 5Min, 15Min, 1H, 1D
        extended_hours: Include extended hours data
    """
    client = get_trading_client()
    request = GetPortfolioHistoryRequest(
        period=period,
        timeframe=timeframe,
        extended_hours=extended_hours,
    )
    history = client.get_portfolio_history(request)

    return {
        "timestamps": history.timestamp,
        "equity": history.equity,
        "profit_loss": history.profit_loss,
        "profit_loss_pct": history.profit_loss_pct,
        "base_value": history.base_value,
    }


def calculate_returns(period: str = "1M"):
    """Calculate portfolio returns for a given period."""
    history = get_portfolio_history(period=period)

    if not history["equity"] or len(history["equity"]) < 2:
        return None

    start_value = history["equity"][0]
    end_value = history["equity"][-1]

    total_return = end_value - start_value
    total_return_pct = (total_return / start_value) * 100 if start_value else 0

    # Calculate daily returns
    daily_returns = []
    for i in range(1, len(history["equity"])):
        prev = history["equity"][i - 1]
        curr = history["equity"][i]
        if prev:
            daily_returns.append((curr - prev) / prev * 100)

    avg_daily_return = sum(daily_returns) / len(daily_returns) if daily_returns else 0

    # Find best and worst days
    best_day = max(daily_returns) if daily_returns else 0
    worst_day = min(daily_returns) if daily_returns else 0

    return {
        "period": period,
        "start_value": start_value,
        "end_value": end_value,
        "total_return": total_return,
        "total_return_pct": total_return_pct,
        "avg_daily_return_pct": avg_daily_return,
        "best_day_pct": best_day,
        "worst_day_pct": worst_day,
        "data_points": len(history["equity"]),
    }


def get_daily_pnl():
    """Get today's P&L."""
    account = get_account_snapshot()

    today_pnl = account["equity"] - account["last_equity"]
    today_pnl_pct = (today_pnl / account["last_equity"]) * 100 if account["last_equity"] else 0

    return {
        "date": datetime.now().strftime("%Y-%m-%d"),
        "current_equity": account["equity"],
        "previous_close_equity": account["last_equity"],
        "daily_pnl": today_pnl,
        "daily_pnl_pct": today_pnl_pct,
    }


def get_activity_history(limit: int = 50):
    """Get account activity history (trades/fills)."""
    from account import get_orders
    orders = get_orders(status="closed", limit=limit)
    return orders


if __name__ == "__main__":
    print("=== Portfolio Tracking ===\n")

    # Current snapshot
    snapshot = get_account_snapshot()
    print("--- Account Snapshot ---")
    print(f"  Portfolio Value: ${snapshot['portfolio_value']:,.2f}")
    print(f"  Cash: ${snapshot['cash']:,.2f}")
    print(f"  Equity: ${snapshot['equity']:,.2f}")
    print(f"  Buying Power: ${snapshot['buying_power']:,.2f}")
    print(f"  Day Trades: {snapshot['daytrade_count']}")

    # Daily P&L
    print("\n--- Daily P&L ---")
    daily = get_daily_pnl()
    print(f"  Date: {daily['date']}")
    print(f"  Previous Close: ${daily['previous_close_equity']:,.2f}")
    print(f"  Current Equity: ${daily['current_equity']:,.2f}")
    print(f"  Daily P&L: ${daily['daily_pnl']:+,.2f} ({daily['daily_pnl_pct']:+.2f}%)")

    # Period returns
    print("\n--- Period Returns ---")
    for period in ["1W", "1M"]:
        returns = calculate_returns(period)
        if returns:
            print(f"\n  {period}:")
            print(f"    Total Return: ${returns['total_return']:+,.2f} ({returns['total_return_pct']:+.2f}%)")
            print(f"    Avg Daily: {returns['avg_daily_return_pct']:+.2f}%")
            print(f"    Best Day: {returns['best_day_pct']:+.2f}%")
            print(f"    Worst Day: {returns['worst_day_pct']:+.2f}%")

    # Recent activity
    print("\n--- Recent Activity ---")
    activities = get_activity_history(limit=5)
    if activities:
        for order in activities:
            print(f"  {order.symbol}: {order.side} {order.qty} @ {order.filled_avg_price} - {order.status}")
    else:
        print("  No recent activity")
