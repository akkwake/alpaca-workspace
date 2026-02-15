from datetime import datetime, timedelta
from alpaca.data.historical import StockHistoricalDataClient
from alpaca.data.live import StockDataStream
from alpaca.data.requests import (
    StockLatestQuoteRequest,
    StockBarsRequest,
    StockTradesRequest,
    StockLatestTradeRequest,
)
from alpaca.data.timeframe import TimeFrame
from alpaca.data.enums import DataFeed
from config import get_alpaca_credentials


def get_data_client():
    """Get authenticated stock data client."""
    creds = get_alpaca_credentials()
    return StockHistoricalDataClient(
        api_key=creds["api_key"],
        secret_key=creds["secret_key"],
    )


def get_latest_quote(symbol: str):
    """Get the latest quote for a symbol."""
    client = get_data_client()
    request = StockLatestQuoteRequest(symbol_or_symbols=symbol, feed=DataFeed.IEX)
    quotes = client.get_stock_latest_quote(request)
    return quotes[symbol]


def get_latest_trade(symbol: str):
    """Get the latest trade for a symbol."""
    client = get_data_client()
    request = StockLatestTradeRequest(symbol_or_symbols=symbol, feed=DataFeed.IEX)
    trades = client.get_stock_latest_trade(request)
    return trades[symbol]


def get_bars(symbol: str, timeframe: TimeFrame = TimeFrame.Day, days: int = 30):
    """Get historical bars for a symbol."""
    client = get_data_client()
    end = datetime.now()
    start = end - timedelta(days=days)

    request = StockBarsRequest(
        symbol_or_symbols=symbol,
        timeframe=timeframe,
        start=start,
        end=end,
        feed=DataFeed.IEX,
    )
    bars = client.get_stock_bars(request)
    return bars[symbol]


def get_trades(symbol: str, days: int = 1, limit: int = 100):
    """Get recent trades for a symbol."""
    client = get_data_client()
    end = datetime.now()
    start = end - timedelta(days=days)

    request = StockTradesRequest(
        symbol_or_symbols=symbol,
        start=start,
        end=end,
        limit=limit,
        feed=DataFeed.IEX,
    )
    trades = client.get_stock_trades(request)
    return trades[symbol]


def get_stream_client():
    """Get a streaming data client for real-time data."""
    creds = get_alpaca_credentials()
    return StockDataStream(
        api_key=creds["api_key"],
        secret_key=creds["secret_key"],
        feed=DataFeed.IEX,
    )


if __name__ == "__main__":
    # Test market data functions
    symbol = "AAPL"

    print(f"=== Market Data for {symbol} ===\n")

    # Latest quote
    quote = get_latest_quote(symbol)
    print(f"Latest Quote:")
    print(f"  Bid: ${quote.bid_price} x {quote.bid_size}")
    print(f"  Ask: ${quote.ask_price} x {quote.ask_size}")
    print(f"  Time: {quote.timestamp}\n")

    # Latest trade
    trade = get_latest_trade(symbol)
    print(f"Latest Trade:")
    print(f"  Price: ${trade.price}")
    print(f"  Size: {trade.size}")
    print(f"  Time: {trade.timestamp}\n")

    # Recent bars
    bars = get_bars(symbol, TimeFrame.Day, days=5)
    print(f"Recent Daily Bars:")
    for bar in bars:
        print(f"  {bar.timestamp.date()}: O=${bar.open} H=${bar.high} L=${bar.low} C=${bar.close} V={bar.volume}")
