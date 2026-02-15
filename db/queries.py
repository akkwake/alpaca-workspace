import json
from datetime import datetime, date
from db.connection import get_pool


async def insert_signal(signal_data: dict) -> int:
    """Insert a signal into the signals table. Returns the new signal ID."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        row_id = await conn.fetchval(
            """
            INSERT INTO signals (source, symbol, action, price, stop_loss,
                                 take_profit, quantity, strategy, confidence, raw_payload)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id
            """,
            signal_data.get("source", "tradingview"),
            signal_data["symbol"],
            signal_data["action"],
            signal_data.get("price"),
            signal_data.get("stop_loss"),
            signal_data.get("take_profit"),
            signal_data.get("quantity"),
            signal_data.get("strategy"),
            signal_data.get("confidence"),
            json.dumps(signal_data.get("raw_payload", {})),
        )
    return row_id


async def get_signals(
    symbol: str | None = None,
    since: datetime | None = None,
    processed: bool | None = None,
    limit: int = 50,
) -> list[dict]:
    """Query signals with optional filters."""
    pool = await get_pool()
    conditions = []
    params = []
    idx = 1

    if symbol is not None:
        conditions.append(f"symbol = ${idx}")
        params.append(symbol)
        idx += 1
    if since is not None:
        conditions.append(f"timestamp >= ${idx}")
        params.append(since)
        idx += 1
    if processed is not None:
        conditions.append(f"processed = ${idx}")
        params.append(processed)
        idx += 1

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    params.append(limit)

    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"SELECT * FROM signals {where} ORDER BY timestamp DESC LIMIT ${idx}",
            *params,
        )
    return [dict(r) for r in rows]


async def mark_signal_processed(signal_id: int) -> bool:
    """Mark a signal as processed. Returns True if updated."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.execute(
            "UPDATE signals SET processed = TRUE WHERE id = $1", signal_id
        )
    return result == "UPDATE 1"


async def upsert_daily_bars(symbol: str, bars: list[dict]) -> int:
    """Bulk upsert daily bars into market_data_daily. Returns rows affected."""
    if not bars:
        return 0
    pool = await get_pool()
    async with pool.acquire() as conn:
        result = await conn.executemany(
            """
            INSERT INTO market_data_daily (symbol, date, open, high, low, close, volume, source)
            VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ON CONFLICT (symbol, date, source) DO UPDATE
            SET open = EXCLUDED.open, high = EXCLUDED.high, low = EXCLUDED.low,
                close = EXCLUDED.close, volume = EXCLUDED.volume
            """,
            [
                (
                    symbol,
                    b["date"],
                    b["open"],
                    b["high"],
                    b["low"],
                    b["close"],
                    b["volume"],
                    b.get("source", "alpaca"),
                )
                for b in bars
            ],
        )
    return len(bars)


async def get_daily_bars(
    symbol: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict]:
    """Query historical daily bars for a symbol."""
    pool = await get_pool()
    conditions = ["symbol = $1"]
    params: list = [symbol]
    idx = 2

    if start_date is not None:
        conditions.append(f"date >= ${idx}")
        params.append(start_date)
        idx += 1
    if end_date is not None:
        conditions.append(f"date <= ${idx}")
        params.append(end_date)
        idx += 1

    where = " AND ".join(conditions)
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            f"SELECT * FROM market_data_daily WHERE {where} ORDER BY date ASC",
            *params,
        )
    return [dict(r) for r in rows]
