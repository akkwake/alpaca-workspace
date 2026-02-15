from market_data import get_bars, get_latest_quote
from positions import get_all_positions
from account import get_orders
from trading import stop_order
from risk_config import get_risk_params


def _calculate_atr(bars, period=14):
    """Calculate Average True Range from bar data."""
    if len(bars) < 2:
        return 0.0

    true_ranges = []
    for i in range(1, len(bars)):
        high = float(bars[i].high)
        low = float(bars[i].low)
        prev_close = float(bars[i - 1].close)

        tr = max(
            high - low,
            abs(high - prev_close),
            abs(low - prev_close),
        )
        true_ranges.append(tr)

    if not true_ranges:
        return 0.0

    # Use last `period` values, or all if fewer
    recent = true_ranges[-period:]
    return sum(recent) / len(recent)


def calculate_stop_levels(symbol, method="atr", **kwargs):
    """
    Calculate stop-loss price levels.

    Methods:
        "fixed_pct" — fixed percentage below current price (default 2%)
        "atr" — ATR-based stop (default 2x ATR)
    """
    quote = get_latest_quote(symbol)
    current_price = float(quote.ask_price) or float(quote.bid_price)

    if method == "fixed_pct":
        pct = kwargs.get("pct", 2.0)
        stop_price = round(current_price * (1 - pct / 100), 2)
        distance_pct = pct
    elif method == "atr":
        multiplier = kwargs.get("multiplier", 2.0)
        days = kwargs.get("days", 30)
        period = kwargs.get("period", 14)

        bars = get_bars(symbol, days=days)
        atr = _calculate_atr(bars, period=period)

        stop_price = round(current_price - (atr * multiplier), 2)
        distance_pct = round((current_price - stop_price) / current_price * 100, 2) if current_price > 0 else 0
    else:
        raise ValueError(f"Unknown stop method: {method}")

    return {
        "symbol": symbol,
        "current_price": round(current_price, 2),
        "stop_price": stop_price,
        "method": method,
        "distance_pct": distance_pct,
    }


def check_stops_needed():
    """Find positions that don't have active stop orders."""
    positions = get_all_positions()
    open_orders = get_orders(status="open")

    # Collect symbols that have stop orders
    symbols_with_stops = set()
    for order in open_orders:
        if order.type and "stop" in str(order.type).lower():
            symbols_with_stops.add(order.symbol)

    unprotected = []
    for pos in positions:
        if pos.symbol not in symbols_with_stops:
            unprotected.append({
                "symbol": pos.symbol,
                "qty": float(pos.qty),
                "current_price": float(pos.current_price),
                "avg_entry_price": float(pos.avg_entry_price),
                "side": str(pos.side),
            })

    return unprotected


def place_stop_for_position(symbol, stop_price):
    """
    Place a stop order for a position.

    In "active" mode: places the order.
    In "advisory" mode: returns the recommendation without placing.
    """
    params = get_risk_params()
    mode = params["stop_loss_mode"]

    # Look up position details
    positions = get_all_positions()
    pos = None
    for p in positions:
        if p.symbol == symbol:
            pos = p
            break

    if not pos:
        return {"error": f"No open position for {symbol}"}

    qty = float(pos.qty)
    recommendation = {
        "symbol": symbol,
        "qty": qty,
        "stop_price": stop_price,
        "mode": mode,
    }

    if mode == "active":
        order = stop_order(symbol, qty, stop_price, side="sell")
        recommendation["order_id"] = str(order.id)
        recommendation["status"] = "placed"
    else:
        recommendation["status"] = "advisory"

    return recommendation


def manage_all_stops(method="atr", **kwargs):
    """Check all positions and place/advise stops for unprotected ones."""
    unprotected = check_stops_needed()
    results = []

    for pos in unprotected:
        levels = calculate_stop_levels(pos["symbol"], method=method, **kwargs)
        result = place_stop_for_position(pos["symbol"], levels["stop_price"])
        result["stop_levels"] = levels
        results.append(result)

    return results


if __name__ == "__main__":
    print("=== Stop-Loss Management ===\n")

    params = get_risk_params()
    print(f"Mode: {params['stop_loss_mode']}\n")

    print("--- Unprotected Positions ---")
    unprotected = check_stops_needed()
    if unprotected:
        for pos in unprotected:
            print(f"  {pos['symbol']}: {pos['qty']} shares @ ${pos['current_price']:,.2f} (entry: ${pos['avg_entry_price']:,.2f})")

            levels = calculate_stop_levels(pos["symbol"])
            print(f"    Recommended stop: ${levels['stop_price']:,.2f} ({levels['method']}, -{levels['distance_pct']:.1f}%)")
    else:
        print("  All positions have stop orders (or no positions open)")

    print("\n--- Stop-Loss Functions ---")
    print("  calculate_stop_levels(symbol, method) - Calculate stop prices")
    print("  check_stops_needed() - Find unprotected positions")
    print("  place_stop_for_position(symbol, stop_price) - Place/advise stop")
    print("  manage_all_stops(method) - Handle all unprotected positions")
