import asyncio
from contextlib import asynccontextmanager
from functools import wraps
import asyncpg
from elasticsearch import AsyncElasticsearch
from fastapi import FastAPI
from app.core.config import settings
from app.core.logger import logger
from app.core.elasticsearch import ES_URL
from app.services.search_service import create_index_if_not_exists

_pool = None
DB_URL = settings.prod_database_url if settings.is_production else settings.database_url
es_client = None


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
    """Manages the startup and shutdown of the database pool and Elastic search(added later)."""

    # 1. POSTGRES STARTUP
    max_retry = 5
    delay = 1

    global _pool

    for attempt in range(1, max_retry + 1):
        try:
            logger.info(f"Connecting to Postgres DB ({attempt}/{max_retry})...")
            # Initialize the pool once on startup
            _pool = await asyncpg.create_pool(
                dsn=DB_URL,
                min_size=1,  # start with 1 connection
                max_size=5,  # never exceed 5 — well under Supabase's 15 limit
                ssl="require",
            )  # Supabase requires SSL)

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

    # 2. ELASTICSEARCH STARTUP
    es_retry = 10
    es_delay = 2

    for attempt in range(1, es_retry + 1):
        try:
            logger.info(f"Connecting to Elasticsearch ({attempt}/{es_retry})...")

            # asyncio creates a fresh event loop and close it later. a globally-created async client stays attached to the old closed loop
            # later requests crash with
            global es_client
            es_client = AsyncElasticsearch([ES_URL])

            if await es_client.ping():
                await create_index_if_not_exists()
                logger.info("Elasticsearch ready + index verified")
                break

        except Exception as e:
            logger.warning(f"Elasticsearch not ready: {e}")

        if attempt == es_retry:
            logger.critical("Elasticsearch failed permanently")
            # raise RuntimeError("ES startup failed")
            pass  # fail gracefully in render

        await asyncio.sleep(es_delay)

    yield  # Pauses or suspends the function at this point, while the app runs

    # cleanup on shutdown
    if es_client:
        await es_client.close()

    if _pool:
        await _pool.close()
        logger.info("Database pool closed safely")
