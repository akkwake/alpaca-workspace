from alpaca.trading.client import TradingClient
from alpaca.trading.requests import ClosePositionRequest
from config import get_alpaca_credentials


def get_trading_client():
    """Get authenticated trading client."""
    creds = get_alpaca_credentials()
    return TradingClient(
        api_key=creds["api_key"],
        secret_key=creds["secret_key"],
        paper=creds["paper"],
    )


def get_all_positions():
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


def close_position(symbol: str, qty: float = None, percentage: float = None):
    """Close a position (fully or partially)."""
    client = get_trading_client()

    if percentage:
        request = ClosePositionRequest(percentage=str(percentage))
    elif qty:
        request = ClosePositionRequest(qty=str(qty))
    else:
        request = ClosePositionRequest()

    return client.close_position(symbol, request)


def close_all_positions(cancel_orders: bool = True):
    """Close all positions."""
    client = get_trading_client()
    return client.close_all_positions(cancel_orders=cancel_orders)


def get_position_pnl(symbol: str):
    """Get P&L for a specific position."""
    pos = get_position(symbol)
    if not pos:
        return None

    return {
        "symbol": pos.symbol,
        "qty": float(pos.qty),
        "avg_entry_price": float(pos.avg_entry_price),
        "current_price": float(pos.current_price),
        "market_value": float(pos.market_value),
        "cost_basis": float(pos.cost_basis),
        "unrealized_pl": float(pos.unrealized_pl),
        "unrealized_pl_pct": float(pos.unrealized_plpc) * 100,
        "unrealized_intraday_pl": float(pos.unrealized_intraday_pl),
        "unrealized_intraday_pl_pct": float(pos.unrealized_intraday_plpc) * 100,
        "side": str(pos.side),
    }


def get_portfolio_summary():
    """Get a summary of all positions."""
    positions = get_all_positions()

    if not positions:
        return {"total_positions": 0, "positions": []}

    summary = []
    total_value = 0
    total_pl = 0
    total_cost = 0

    for pos in positions:
        pl = float(pos.unrealized_pl)
        pl_pct = float(pos.unrealized_plpc) * 100
        market_value = float(pos.market_value)
        cost = float(pos.cost_basis)

        summary.append({
            "symbol": pos.symbol,
            "qty": float(pos.qty),
            "current_price": float(pos.current_price),
            "market_value": market_value,
            "unrealized_pl": pl,
            "unrealized_pl_pct": pl_pct,
        })

        total_value += market_value
        total_pl += pl
        total_cost += cost

    return {
        "total_positions": len(positions),
        "total_market_value": total_value,
        "total_cost_basis": total_cost,
        "total_unrealized_pl": total_pl,
        "total_unrealized_pl_pct": (total_pl / total_cost * 100) if total_cost else 0,
        "positions": summary,
    }


if __name__ == "__main__":
    print("=== Position Management ===\n")

    summary = get_portfolio_summary()

    print(f"Total Positions: {summary['total_positions']}")
    if summary['total_positions'] > 0:
        print(f"Total Market Value: ${summary['total_market_value']:,.2f}")
        print(f"Total Cost Basis: ${summary['total_cost_basis']:,.2f}")
        print(f"Total Unrealized P&L: ${summary['total_unrealized_pl']:+,.2f} ({summary['total_unrealized_pl_pct']:+.2f}%)")

        print("\n--- Individual Positions ---")
        for pos in summary['positions']:
            print(f"\n  {pos['symbol']}:")
            print(f"    Qty: {pos['qty']}")
            print(f"    Current Price: ${pos['current_price']:,.2f}")
            print(f"    Market Value: ${pos['market_value']:,.2f}")
            print(f"    Unrealized P&L: ${pos['unrealized_pl']:+,.2f} ({pos['unrealized_pl_pct']:+.2f}%)")
    else:
        print("No open positions")

    print("\n--- Position Functions ---")
    print("  get_all_positions() - Get all positions")
    print("  get_position(symbol) - Get specific position")
    print("  close_position(symbol, qty, percentage) - Close position")
    print("  close_all_positions() - Close all positions")
    print("  get_position_pnl(symbol) - Get P&L details")
    print("  get_portfolio_summary() - Get portfolio summary")
