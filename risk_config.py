import os
from dotenv import load_dotenv

load_dotenv()


def get_risk_params():
    """Load risk management parameters from environment variables."""
    return {
        "max_position_pct": float(os.getenv("RISK_MAX_POSITION_PCT", "20")),
        "max_portfolio_risk_pct": float(os.getenv("RISK_MAX_PORTFOLIO_RISK_PCT", "2")),
        "max_daily_loss_pct": float(os.getenv("RISK_MAX_DAILY_LOSS_PCT", "3")),
        "max_drawdown_pct": float(os.getenv("RISK_MAX_DRAWDOWN_PCT", "10")),
        "stop_loss_mode": os.getenv("RISK_STOP_LOSS_MODE", "advisory"),
    }


if __name__ == "__main__":
    print("=== Risk Parameters ===\n")

    params = get_risk_params()
    print(f"  Max Position Size: {params['max_position_pct']}% of portfolio")
    print(f"  Max Portfolio Risk Per Trade: {params['max_portfolio_risk_pct']}% of equity")
    print(f"  Max Daily Loss Limit: {params['max_daily_loss_pct']}% of equity")
    print(f"  Max Drawdown: {params['max_drawdown_pct']}% from peak")
    print(f"  Stop-Loss Mode: {params['stop_loss_mode']}")
