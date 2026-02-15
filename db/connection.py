import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

_pool = None


async def get_pool():
    """Get or create the asyncpg connection pool (singleton)."""
    global _pool
    if _pool is None or _pool._closed:
        _pool = await asyncpg.create_pool(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "alpaca"),
            user=os.getenv("DB_USER", "alpaca"),
            password=os.getenv("DB_PASSWORD", ""),
            min_size=2,
            max_size=10,
        )
    return _pool


async def close_pool():
    """Close the connection pool."""
    global _pool
    if _pool and not _pool._closed:
        await _pool.close()
        _pool = None


if __name__ == "__main__":
    import asyncio

    async def test_connection():
        print("=== Database Connection Test ===\n")
        try:
            pool = await get_pool()
            async with pool.acquire() as conn:
                version = await conn.fetchval("SELECT version()")
                print(f"Connected: {version}")

                # Check tables exist
                tables = await conn.fetch(
                    "SELECT tablename FROM pg_tables WHERE schemaname = 'public'"
                )
                print(f"Tables: {[t['tablename'] for t in tables]}")
        except Exception as e:
            print(f"Connection failed: {e}")
        finally:
            await close_pool()

    asyncio.run(test_connection())
