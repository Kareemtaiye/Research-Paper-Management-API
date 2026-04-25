import asyncio
from contextlib import asynccontextmanager
from functools import wraps
import asyncpg
from fastapi import FastAPI
from app.core.config import settings
from app.core.logger import logger

_pool = None


async def get_pool():
    """Returns the globally managed connection pool."""
    global _pool
    if _pool is None:
        logger.error("Attempting to access pool")
        raise RuntimeError("Database pool not created. Did you forget to use lifespan?")
    return _pool


# Gets a connection from the pool
async def get_conn():
    pool = await get_pool()
    async with pool.acquire() as conn:
        yield conn


def with_connection(func):
    """Decorator to automatically provide a db connection to class methods(when one is not provided)."""

    @wraps(func)
    async def wrapper(self, *args, **kwargs):
        # 1. Use existing connection if passed (very important for transactions)
        if "conn" in kwargs and kwargs["conn"] is not None:
            return await func(self, *args, **kwargs)

        # Acquire a fresh connection from the pool if otherwiase
        pool = await get_pool()
        async with pool.acquire() as conn:
            kwargs["conn"] = conn
            return await func(self, *args, **kwargs)

    return wrapper


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manages the startup and shutdown of the database pool."""

    max_retry = 5
    delay = 1

    global _pool

    for attempt in range(1, max_retry + 1):
        try:
            logger.info(f"Connecting to Postgres DB {attempt}/{max_retry})...")
            # Initialize the pool once on startup
            _pool = await asyncpg.create_pool(
                dsn=settings.database_url, max_size=20, ssl=None
            )

            logger.info("Database pool created successfully")
            break  # End loop if successful
        except Exception as e:
            if attempt == max_retry:
                logger.critical(
                    f"Final attempt to failed. Could not connect to Postgres DB: {e}"
                )
                raise  # Crash if we still cant connect after 5 times

            logger.warning(
                f"Connecting to Postgres DB failed {e}. Retrying in {delay}s.."
            )
            await asyncio.sleep(delay)
            delay *= 2  # Expon Backoff

    yield  # Pauses or suspends the function at this point, while the app runs

    # cleanup on shutdown
    if _pool:
        await _pool.close()
        logger.info("Database pool closed safely")
