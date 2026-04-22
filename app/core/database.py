from contextlib import asynccontextmanager
from functools import wraps
import asyncpg
from fastapi import FastAPI
from app.core.config import settings

_pool = None


async def get_pool():
    """Returns the globally managed connection pool."""
    global _pool
    if _pool is None:
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
    global _pool
    # Initialize the pool once on startup
    _pool = await asyncpg.create_pool(dsn=settings.database_url, max_size=20, ssl=None)

    yield  # Pauses or suspends the function at this point, while the app runs

    # cleanup on shutdown
    await _pool.close()
    print("DB connection closed")
