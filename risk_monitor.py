from portfolio import get_account_snapshot, get_daily_pnl, get_portfolio_history
from positions import get_portfolio_summary
from market_data import get_latest_quote
from risk_config import get_risk_params


def check_position_concentration():
    """Check if any position exceeds the max position size limit."""
    params = get_risk_params()
    limit = params["max_position_pct"]

    account = get_account_snapshot()
    equity = account["equity"]

    summary = get_portfolio_summary()
    violations = []
    position_details = []

    for pos in summary.get("positions", []):
        pct = (pos["market_value"] / equity * 100) if equity > 0 else 0
        entry = {
            "symbol": pos["symbol"],
            "pct_of_portfolio": round(pct, 2),
            "limit": limit,
            "market_value": pos["market_value"],
        }
        position_details.append(entry)
        if pct > limit:
            violations.append(entry)

    return {"violations": violations, "positions": position_details}


def check_daily_pnl_limit():
    """Check if daily P&L has breached the loss limit."""
    params = get_risk_params()
    limit_pct = params["max_daily_loss_pct"]

    daily = get_daily_pnl()
    daily_pnl_pct = daily["daily_pnl_pct"]

    return {
        "breached": daily_pnl_pct <= -limit_pct,
        "daily_pnl_pct": round(daily_pnl_pct, 2),
        "limit_pct": limit_pct,
        "daily_pnl": round(daily["daily_pnl"], 2),
    }


def check_drawdown():
    """Check if portfolio drawdown has breached the max drawdown limit."""
    params = get_risk_params()
    limit_pct = params["max_drawdown_pct"]

    history = get_portfolio_history(period="3M", timeframe="1D")
    equities = history.get("equity", [])

    if not equities:
        return {
            "current_drawdown_pct": 0.0,
            "peak_equity": 0.0,
            "current_equity": 0.0,
            "breached": False,
        }

    # Filter out None values
    valid_equities = [e for e in equities if e is not None]
    if not valid_equities:
        return {
            "current_drawdown_pct": 0.0,
            "peak_equity": 0.0,
            "current_equity": 0.0,
            "breached": False,
        }

    peak = max(valid_equities)
    current = valid_equities[-1]
    drawdown_pct = ((peak - current) / peak * 100) if peak > 0 else 0

    return {
        "current_drawdown_pct": round(drawdown_pct, 2),
        "peak_equity": round(peak, 2),
        "current_equity": round(current, 2),
        "breached": drawdown_pct >= limit_pct,
        "limit_pct": limit_pct,
    }


def check_indicator_threshold(symbol, indicator_name, threshold, direction="above"):
    """
    Check if a price-based threshold has been breached.

    Extensible hook for future technical indicator alerts.
    Currently supports simple price thresholds.
    """
    quote = get_latest_quote(symbol)
    current_value = float(quote.ask_price) or float(quote.bid_price)

    if direction == "above":
        breached = current_value > threshold
    else:
        breached = current_value < threshold

    return {
        "symbol": symbol,
        "indicator": indicator_name,
        "breached": breached,
        "current_value": round(current_value, 2),
        "threshold": threshold,
        "direction": direction,
    }


def get_portfolio_risk_summary():
    """Run all risk checks and return a unified summary."""
    concentration = check_position_concentration()
    daily_pnl = check_daily_pnl_limit()
    drawdown = check_drawdown()

    any_breach = bool(
        concentration["violations"]
        or daily_pnl["breached"]
        or drawdown["breached"]
    )

    return {
        "has_breaches": any_breach,
        "concentration": concentration,
        "daily_pnl": daily_pnl,
        "drawdown": drawdown,
    }


if __name__ == "__main__":
    print("=== Portfolio Risk Monitor ===\n")

    summary = get_portfolio_risk_summary()

    print("--- Position Concentration ---")
    for pos in summary["concentration"]["positions"]:
        flag = " *** OVER LIMIT ***" if pos["pct_of_portfolio"] > pos["limit"] else ""
        print(f"  {pos['symbol']}: {pos['pct_of_portfolio']:.1f}% of portfolio (limit: {pos['limit']}%){flag}")
    if not summary["concentration"]["positions"]:
        print("  No open positions")

    print("\n--- Daily P&L ---")
    dpnl = summary["daily_pnl"]
    status = "BREACHED" if dpnl["breached"] else "OK"
    print(f"  Daily P&L: {dpnl['daily_pnl_pct']:+.2f}% (${dpnl['daily_pnl']:+,.2f})")
    print(f"  Limit: -{dpnl['limit_pct']}% | Status: {status}")

    print("\n--- Drawdown ---")
    dd = summary["drawdown"]
    status = "BREACHED" if dd["breached"] else "OK"
    print(f"  Current Drawdown: {dd['current_drawdown_pct']:.2f}%")
    print(f"  Peak Equity: ${dd['peak_equity']:,.2f}")
    print(f"  Current Equity: ${dd['current_equity']:,.2f}")
    print(f"  Limit: {dd.get('limit_pct', 'N/A')}% | Status: {status}")

    print(f"\n--- Overall: {'BREACHES DETECTED' if summary['has_breaches'] else 'ALL CLEAR'} ---")
