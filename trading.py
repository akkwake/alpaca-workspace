from alpaca.trading.client import TradingClient
from alpaca.trading.requests import (
    MarketOrderRequest,
    LimitOrderRequest,
    StopOrderRequest,
    StopLimitOrderRequest,
    TrailingStopOrderRequest,
    TakeProfitRequest,
    StopLossRequest,
    ReplaceOrderRequest,
)
from alpaca.trading.enums import OrderSide, TimeInForce, OrderClass
from config import get_alpaca_credentials


def get_trading_client():
    """Get authenticated trading client."""
    creds = get_alpaca_credentials()
    return TradingClient(
        api_key=creds["api_key"],
        secret_key=creds["secret_key"],
        paper=creds["paper"],
    )


# --- Basic Order Types ---

def market_order(symbol: str, qty: float, side: str = "buy"):
    """Place a market order."""
    client = get_trading_client()
    request = MarketOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL,
        time_in_force=TimeInForce.DAY,
    )
    return client.submit_order(request)


def limit_order(symbol: str, qty: float, limit_price: float, side: str = "buy"):
    """Place a limit order."""
    client = get_trading_client()
    request = LimitOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL,
        time_in_force=TimeInForce.DAY,
        limit_price=limit_price,
    )
    return client.submit_order(request)


def stop_order(symbol: str, qty: float, stop_price: float, side: str = "sell"):
    """Place a stop order."""
    client = get_trading_client()
    request = StopOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL,
        time_in_force=TimeInForce.DAY,
        stop_price=stop_price,
    )
    return client.submit_order(request)


def stop_limit_order(symbol: str, qty: float, stop_price: float, limit_price: float, side: str = "sell"):
    """Place a stop-limit order."""
    client = get_trading_client()
    request = StopLimitOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL,
        time_in_force=TimeInForce.DAY,
        stop_price=stop_price,
        limit_price=limit_price,
    )
    return client.submit_order(request)


def trailing_stop_order(symbol: str, qty: float, trail_percent: float = None, trail_price: float = None, side: str = "sell"):
    """Place a trailing stop order."""
    client = get_trading_client()
    request = TrailingStopOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL,
        time_in_force=TimeInForce.DAY,
        trail_percent=trail_percent,
        trail_price=trail_price,
    )
    return client.submit_order(request)


# --- Order Management ---

def get_order(order_id: str):
    """Get order by ID."""
    client = get_trading_client()
    return client.get_order_by_id(order_id)


def cancel_order(order_id: str):
    """Cancel an order by ID."""
    client = get_trading_client()
    client.cancel_order_by_id(order_id)
    return True


def cancel_all_orders():
    """Cancel all open orders."""
    client = get_trading_client()
    return client.cancel_orders()


def replace_order(order_id: str, qty: float = None, limit_price: float = None, stop_price: float = None):
    """Modify an existing order."""
    client = get_trading_client()
    request = ReplaceOrderRequest(
        qty=qty,
        limit_price=limit_price,
        stop_price=stop_price,
    )
    return client.replace_order_by_id(order_id, request)


# --- Bracket Orders ---

def bracket_order(
    symbol: str,
    qty: float,
    side: str = "buy",
    take_profit_price: float = None,
    stop_loss_price: float = None,
    limit_price: float = None,
):
    """Place a bracket order with take-profit and stop-loss."""
    client = get_trading_client()

    order_side = OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL

    if limit_price:
        request = LimitOrderRequest(
            symbol=symbol,
            qty=qty,
            side=order_side,
            time_in_force=TimeInForce.DAY,
            limit_price=limit_price,
            order_class=OrderClass.BRACKET,
            take_profit=TakeProfitRequest(limit_price=take_profit_price) if take_profit_price else None,
            stop_loss=StopLossRequest(stop_price=stop_loss_price) if stop_loss_price else None,
        )
    else:
        request = MarketOrderRequest(
            symbol=symbol,
            qty=qty,
            side=order_side,
            time_in_force=TimeInForce.DAY,
            order_class=OrderClass.BRACKET,
            take_profit=TakeProfitRequest(limit_price=take_profit_price) if take_profit_price else None,
            stop_loss=StopLossRequest(stop_price=stop_loss_price) if stop_loss_price else None,
        )

    return client.submit_order(request)


def oco_order(symbol: str, qty: float, take_profit_price: float, stop_loss_price: float, side: str = "sell"):
    """Place an OCO (one-cancels-other) order."""
    client = get_trading_client()

    request = LimitOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL,
        time_in_force=TimeInForce.DAY,
        limit_price=take_profit_price,
        order_class=OrderClass.OCO,
        stop_loss=StopLossRequest(stop_price=stop_loss_price),
    )
    return client.submit_order(request)


def oto_order(symbol: str, qty: float, limit_price: float, stop_loss_price: float, side: str = "buy"):
    """Place an OTO (one-triggers-other) order."""
    client = get_trading_client()

    request = LimitOrderRequest(
        symbol=symbol,
        qty=qty,
        side=OrderSide.BUY if side.lower() == "buy" else OrderSide.SELL,
        time_in_force=TimeInForce.DAY,
        limit_price=limit_price,
        order_class=OrderClass.OTO,
        stop_loss=StopLossRequest(stop_price=stop_loss_price),
    )
    return client.submit_order(request)


if __name__ == "__main__":
    from account import get_orders

    print("=== Trading Module ===\n")
    print("Available order functions:")
    print("  - market_order(symbol, qty, side)")
    print("  - limit_order(symbol, qty, limit_price, side)")
    print("  - stop_order(symbol, qty, stop_price, side)")
    print("  - stop_limit_order(symbol, qty, stop_price, limit_price, side)")
    print("  - trailing_stop_order(symbol, qty, trail_percent/trail_price, side)")
    print("  - bracket_order(symbol, qty, side, take_profit_price, stop_loss_price)")
    print("  - oco_order(symbol, qty, take_profit_price, stop_loss_price, side)")
    print("  - oto_order(symbol, qty, limit_price, stop_loss_price, side)")
    print("\nOrder management:")
    print("  - get_order(order_id)")
    print("  - cancel_order(order_id)")
    print("  - cancel_all_orders()")
    print("  - replace_order(order_id, qty, limit_price, stop_price)")

    print("\n=== Current Open Orders ===")
    orders = get_orders(status="open")
    if orders:
        for order in orders:
            print(f"  {order.id}: {order.symbol} {order.side} {order.qty} @ {order.type} - {order.status}")
    else:
        print("  No open orders")
