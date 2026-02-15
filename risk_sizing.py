from portfolio import get_account_snapshot
from market_data import get_latest_quote
from risk_config import get_risk_params


def fixed_fractional_size(symbol, side, stop_price, risk_pct=None):
    """
    Calculate position size using fixed fractional method.

    Sizes position so that if stop is hit, loss equals risk_pct of equity.
    qty = (equity * risk_pct) / |entry_price - stop_price|
    """
    params = get_risk_params()
    if risk_pct is None:
        risk_pct = params["max_portfolio_risk_pct"]

    account = get_account_snapshot()
    equity = account["equity"]

    quote = get_latest_quote(symbol)
    entry_price = float(quote.ask_price) if side.lower() == "buy" else float(quote.bid_price)
    if entry_price <= 0:
        entry_price = float(quote.bid_price) if side.lower() == "buy" else float(quote.ask_price)

    risk_per_share = abs(entry_price - stop_price)
    if risk_per_share <= 0:
        return {"qty": 0, "risk_amount": 0.0, "position_value": 0.0, "error": "Stop price too close to entry"}

    risk_amount = equity * (risk_pct / 100)
    qty = int(risk_amount / risk_per_share)

    # Cap at max position size
    max_position_value = equity * (params["max_position_pct"] / 100)
    max_qty = int(max_position_value / entry_price) if entry_price > 0 else 0
    qty = min(qty, max_qty)

    return {
        "qty": qty,
        "risk_amount": round(qty * risk_per_share, 2),
        "position_value": round(qty * entry_price, 2),
        "entry_price": round(entry_price, 2),
        "stop_price": round(stop_price, 2),
        "risk_per_share": round(risk_per_share, 2),
        "method": "fixed_fractional",
    }


def kelly_size(symbol, side, stop_price, win_rate, avg_win, avg_loss):
    """
    Calculate position size using Kelly criterion (half-Kelly).

    Kelly fraction: f = win_rate - ((1 - win_rate) / (avg_win / avg_loss))
    Applies half-Kelly by default for safety, capped at max_position_pct.
    """
    params = get_risk_params()

    if avg_loss <= 0:
        return {"qty": 0, "risk_amount": 0.0, "position_value": 0.0, "error": "avg_loss must be positive"}

    win_loss_ratio = avg_win / avg_loss
    kelly_fraction = win_rate - ((1 - win_rate) / win_loss_ratio)

    # Half-Kelly for safety
    half_kelly = kelly_fraction / 2

    # Don't bet if Kelly is negative
    if half_kelly <= 0:
        return {"qty": 0, "risk_amount": 0.0, "position_value": 0.0, "kelly_fraction": round(kelly_fraction, 4),
                "error": "Negative Kelly — edge insufficient"}

    # Cap at max position pct
    max_fraction = params["max_position_pct"] / 100
    fraction = min(half_kelly, max_fraction)

    account = get_account_snapshot()
    equity = account["equity"]

    quote = get_latest_quote(symbol)
    entry_price = float(quote.ask_price) if side.lower() == "buy" else float(quote.bid_price)
    if entry_price <= 0:
        entry_price = float(quote.bid_price) if side.lower() == "buy" else float(quote.ask_price)

    position_value = equity * fraction
    qty = int(position_value / entry_price) if entry_price > 0 else 0

    risk_per_share = abs(entry_price - stop_price)

    return {
        "qty": qty,
        "risk_amount": round(qty * risk_per_share, 2),
        "position_value": round(qty * entry_price, 2),
        "entry_price": round(entry_price, 2),
        "stop_price": round(stop_price, 2),
        "kelly_fraction": round(kelly_fraction, 4),
        "half_kelly": round(half_kelly, 4),
        "fraction_used": round(fraction, 4),
        "method": "kelly",
    }


def calculate_size(symbol, side, stop_price, method="fixed_fractional", **kwargs):
    """Unified entry point for position sizing."""
    if method == "fixed_fractional":
        return fixed_fractional_size(symbol, side, stop_price, **kwargs)
    elif method == "kelly":
        return kelly_size(symbol, side, stop_price, **kwargs)
    else:
        raise ValueError(f"Unknown sizing method: {method}")


if __name__ == "__main__":
    print("=== Position Sizing Demo ===\n")

    symbol = "AAPL"
    quote = get_latest_quote(symbol)
    price = float(quote.ask_price) or float(quote.bid_price)
    stop = round(price * 0.95, 2)  # 5% below current price

    print(f"Symbol: {symbol}")
    print(f"Current Price: ${price:.2f}")
    print(f"Stop Price: ${stop:.2f}")

    print("\n--- Fixed Fractional ---")
    result = fixed_fractional_size(symbol, "buy", stop)
    for k, v in result.items():
        print(f"  {k}: {v}")

    print("\n--- Kelly Criterion ---")
    result = kelly_size(symbol, "buy", stop, win_rate=0.55, avg_win=2.0, avg_loss=1.0)
    for k, v in result.items():
        print(f"  {k}: {v}")
