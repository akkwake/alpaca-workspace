import argparse
import asyncio
from datetime import date

from alpaca.data.timeframe import TimeFrame

from db.connection import get_pool, close_pool
from db.queries import upsert_daily_bars, get_daily_bars
from market_data import get_bars
from positions import get_all_positions


def _bars_to_dicts(bars) -> list[dict]:
    """Convert Alpaca Bar objects to dicts for DB insertion."""
    return [
        {
            "date": bar.timestamp.date(),
            "open": float(bar.open),
            "high": float(bar.high),
            "low": float(bar.low),
            "close": float(bar.close),
            "volume": int(bar.volume),
            "source": "alpaca",
        }
        for bar in bars
    ]


async def sync_daily_bars(symbols: list[str], days: int = 90):
    """Fetch daily bars from Alpaca and upsert into PostgreSQL."""
    results = {}
    for symbol in symbols:
        try:
            bars = get_bars(symbol, TimeFrame.Day, days=days)
            bar_dicts = _bars_to_dicts(bars)
            count = await upsert_daily_bars(symbol, bar_dicts)
            results[symbol] = {"status": "ok", "bars": count}
            print(f"  {symbol}: synced {count} bars")
        except Exception as e:
            results[symbol] = {"status": "error", "error": str(e)}
            print(f"  {symbol}: error - {e}")
    return results


async def get_sync_status() -> list[dict]:
    """Show last sync date per symbol."""
    pool = await get_pool()
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT symbol, MIN(date) as earliest, MAX(date) as latest, COUNT(*) as bar_count
            FROM market_data_daily
            GROUP BY symbol
            ORDER BY symbol
            """
        )
    return [dict(r) for r in rows]


def _get_position_symbols() -> list[str]:
    """Get symbols from current portfolio positions."""
    try:
        positions = get_all_positions()
        return [p.symbol for p in positions]
    except Exception:
        return []


async def main():
    parser = argparse.ArgumentParser(description="Sync Alpaca market data to PostgreSQL")
    parser.add_argument(
        "--symbols", type=str, default=None,
        help="Comma-separated symbols (default: current positions)",
    )
    parser.add_argument(
        "--days", type=int, default=90,
        help="Days of history to sync (default: 90)",
    )
    parser.add_argument(
        "--status", action="store_true",
        help="Show sync status and exit",
    )
    args = parser.parse_args()

    print("=== Alpaca Data Pipeline ===\n")

    try:
        await get_pool()

        if args.status:
            status = await get_sync_status()
            if not status:
                print("No data synced yet.")
            else:
                print(f"{'Symbol':<8} {'Earliest':<12} {'Latest':<12} {'Bars':>6}")
                print("-" * 40)
                for row in status:
                    print(
                        f"{row['symbol']:<8} {row['earliest']!s:<12} "
                        f"{row['latest']!s:<12} {row['bar_count']:>6}"
                    )
            return

        if args.symbols:
            symbols = [s.strip().upper() for s in args.symbols.split(",")]
        else:
            symbols = _get_position_symbols()
            if not symbols:
                print("No positions found and no --symbols provided.")
                return

        print(f"Syncing {len(symbols)} symbols, {args.days} days of history...\n")
        results = await sync_daily_bars(symbols, days=args.days)

        print(f"\nDone. {sum(1 for r in results.values() if r['status'] == 'ok')}/{len(results)} succeeded.")

    finally:
        await close_pool()


if __name__ == "__main__":
    asyncio.run(main())
