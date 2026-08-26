import redis.asyncio as redis
from app.core.config import settings

REDIS_URL = (
    settings.prod_redis_cache_url
    if settings.is_production
    else settings.redis_cache_url
)

# Only add SSL params for rediss:// URLs
is_ssl = REDIS_URL.startswith("rediss://")

redis_client = redis.from_url(
    REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
    socket_connect_timeout=10,
    socket_timeout=10,
    retry_on_timeout=True,
    health_check_interval=30,
    **({"ssl_cert_reqs": None} if is_ssl else {}),
)
