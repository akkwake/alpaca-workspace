import os
from dotenv import load_dotenv

load_dotenv()


def get_alpaca_credentials():
    """Load Alpaca API credentials from environment variables."""
    api_key = os.getenv("ALPACA_API_KEY")
    secret_key = os.getenv("ALPACA_SECRET_KEY")
    trading_mode = os.getenv("ALPACA_TRADING_MODE", "paper")

    if not api_key or not secret_key:
        raise ValueError(
            "Missing Alpaca credentials. "
            "Set ALPACA_API_KEY and ALPACA_SECRET_KEY environment variables. "
            "See .env.example for reference."
        )

    return {
        "api_key": api_key,
        "secret_key": secret_key,
        "paper": trading_mode.lower() == "paper",
    }
