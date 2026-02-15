import sys
from risk_config import get_risk_params
from risk_monitor import get_portfolio_risk_summary
from risk_stoploss import check_stops_needed, calculate_stop_levels
from notifications import notify_risk_breach, notify_daily_summary


def run_risk_check(notify=False):
    """Run all risk checks and optionally send notifications."""
    params = get_risk_params()
    summary = get_portfolio_risk_summary()
    unprotected = check_stops_needed()

    # Print report
    print("=== Risk Check Report ===\n")

    print("--- Parameters ---")
    print(f"  Max Position: {params['max_position_pct']}%")
    print(f"  Max Risk/Trade: {params['max_portfolio_risk_pct']}%")
    print(f"  Max Daily Loss: {params['max_daily_loss_pct']}%")
    print(f"  Max Drawdown: {params['max_drawdown_pct']}%")
    print(f"  Stop Mode: {params['stop_loss_mode']}")

    print("\n--- Position Concentration ---")
    for pos in summary["concentration"]["positions"]:
        flag = " *** OVER LIMIT ***" if pos["pct_of_portfolio"] > pos["limit"] else ""
        print(f"  {pos['symbol']}: {pos['pct_of_portfolio']:.1f}% (limit: {pos['limit']}%){flag}")
    if not summary["concentration"]["positions"]:
        print("  No open positions")

    print("\n--- Daily P&L ---")
    dpnl = summary["daily_pnl"]
    status = "BREACHED" if dpnl["breached"] else "OK"
    print(f"  P&L: {dpnl['daily_pnl_pct']:+.2f}% (${dpnl['daily_pnl']:+,.2f})")
    print(f"  Limit: -{dpnl['limit_pct']}% | Status: {status}")

    print("\n--- Drawdown ---")
    dd = summary["drawdown"]
    status = "BREACHED" if dd["breached"] else "OK"
    print(f"  Drawdown: {dd['current_drawdown_pct']:.2f}% (peak: ${dd['peak_equity']:,.2f})")
    print(f"  Limit: {dd.get('limit_pct', 'N/A')}% | Status: {status}")

    print("\n--- Unprotected Positions ---")
    if unprotected:
        for pos in unprotected:
            levels = calculate_stop_levels(pos["symbol"])
            print(f"  {pos['symbol']}: {pos['qty']} shares — suggested stop ${levels['stop_price']:,.2f} ({levels['method']}, -{levels['distance_pct']:.1f}%)")
    else:
        print("  All positions protected (or none open)")

    print(f"\n--- Overall: {'BREACHES DETECTED' if summary['has_breaches'] else 'ALL CLEAR'} ---")

    # Send notifications if requested
    if notify:
        print("\n--- Sending Notifications ---")

        # Alert on individual breaches
        if summary["concentration"]["violations"]:
            symbols = ", ".join(v["symbol"] for v in summary["concentration"]["violations"])
            notify_risk_breach("Position Concentration", f"Over-concentrated positions: {symbols}")
            print("  Sent: concentration breach alert")

        if summary["daily_pnl"]["breached"]:
            notify_risk_breach("Daily Loss Limit", f"Daily P&L: {dpnl['daily_pnl_pct']:+.2f}% (limit: -{dpnl['limit_pct']}%)")
            print("  Sent: daily loss breach alert")

        if summary["drawdown"]["breached"]:
            notify_risk_breach("Max Drawdown", f"Drawdown: {dd['current_drawdown_pct']:.2f}% (limit: {dd.get('limit_pct')}%)")
            print("  Sent: drawdown breach alert")

        # Always send daily summary
        notify_daily_summary(summary)
        print("  Sent: daily summary")

    return summary


if __name__ == "__main__":
    notify = "--notify" in sys.argv
    run_risk_check(notify=notify)
