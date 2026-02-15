import os
from contextlib import asynccontextmanager
from datetime import datetime

from dotenv import load_dotenv
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel

from db.connection import get_pool, close_pool
from db.queries import insert_signal, get_signals
from notifications import send_notification

load_dotenv()

WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "")


class TradingViewSignal(BaseModel):
    symbol: str
    action: str  # buy, sell, exit
    price: float | None = None
    stop_loss: float | None = None
    take_profit: float | None = None
    quantity: float | None = None
    strategy: str | None = None
    confidence: float | None = None
    secret: str | None = None  # webhook auth token


@asynccontextmanager
async def lifespan(app: FastAPI):
    await get_pool()
    yield
    await close_pool()


app = FastAPI(title="TradingView Webhook Receiver", lifespan=lifespan)


@app.get("/health")
async def health():
    """Health check endpoint."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        await conn.fetchval("SELECT 1")
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.post("/webhook/tradingview")
async def receive_tradingview(
    signal: TradingViewSignal,
    x_webhook_secret: str | None = Header(None),
):
    """Receive and store a TradingView webhook alert."""
    # Authenticate: check header or payload secret
    provided_secret = x_webhook_secret or signal.secret
    if WEBHOOK_SECRET and provided_secret != WEBHOOK_SECRET:
        raise HTTPException(status_code=401, detail="Invalid webhook secret")

    # Validate action
    valid_actions = {"buy", "sell", "exit"}
    if signal.action.lower() not in valid_actions:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid action '{signal.action}'. Must be one of: {valid_actions}",
        )

    # Build signal data for DB insert
    payload = signal.model_dump()
    payload.pop("secret", None)
    signal_data = {
        "source": "tradingview",
        "symbol": signal.symbol.upper(),
        "action": signal.action.lower(),
        "price": signal.price,
        "stop_loss": signal.stop_loss,
        "take_profit": signal.take_profit,
        "quantity": signal.quantity,
        "strategy": signal.strategy,
        "confidence": signal.confidence,
        "raw_payload": payload,
    }

    signal_id = await insert_signal(signal_data)

    # Send NTFY notification
    try:
        tags = {"buy": "chart_with_upwards_trend", "sell": "chart_with_downwards_trend", "exit": "door"}
        send_notification(
            title=f"TV Signal: {signal.action.upper()} {signal.symbol.upper()}",
            message=(
                f"Action: {signal.action}\n"
                f"Symbol: {signal.symbol.upper()}\n"
                f"Price: {signal.price or 'market'}\n"
                f"Strategy: {signal.strategy or 'N/A'}"
            ),
            priority=4,
            tags=tags.get(signal.action.lower(), "bell"),
            topic_key="NTFY_TOPIC_MOVES",
        )
    except Exception:
        pass  # Don't fail the webhook if notification fails

    return {"status": "received", "signal_id": signal_id}


@app.get("/signals")
async def list_signals(
    symbol: str | None = None,
    limit: int = 20,
    processed: bool | None = None,
):
    """List recent signals for debugging."""
    rows = await get_signals(symbol=symbol, processed=processed, limit=limit)
    # Convert datetime/Decimal fields for JSON serialization
    for row in rows:
        for key, val in row.items():
            if isinstance(val, datetime):
                row[key] = val.isoformat()
            elif hasattr(val, "as_tuple"):  # Decimal
                row[key] = float(val)
    return {"signals": rows, "count": len(rows)}
