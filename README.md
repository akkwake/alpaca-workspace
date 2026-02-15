# Alpaca Trading Environment

Python trading environment for Alpaca Markets API.

## Setup

```bash
cp .env.example .env
# Add your ALPACA_API_KEY and ALPACA_SECRET_KEY to .env

uv run python main.py  # Test connection
```

## Modules

| Module | Purpose |
|--------|---------|
| `market_data.py` | Quotes, bars, trades, streaming |
| `account.py` | Account info, positions, orders |
| `trading.py` | Order placement (market/limit/stop/bracket) |
| `positions.py` | Position management, P&L |
| `portfolio.py` | Portfolio tracking, returns |
| `watchlist.py` | Watchlist management |
| `assets.py` | Asset search & filtering |

## Examples

```python
from trading import market_order, bracket_order
from market_data import get_latest_quote
from positions import close_position

# Get quote
quote = get_latest_quote("AAPL")

# Market buy
order = market_order("AAPL", 10, "buy")

# Bracket order with take-profit and stop-loss
order = bracket_order("AAPL", 10, "buy", take_profit_price=260, stop_loss_price=230)

# Close position
close_position("AAPL")
```

## Run Module Tests

```bash
uv run python market_data.py
uv run python account.py
uv run python positions.py
uv run python portfolio.py
```
