from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.core.redis import redis_client
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.exceptions.schemas import ErrorResponse

# V1
# def regsiter_middleware(app):
#     @app.middleware("http")
#     async def rate_limiter(request: Request, call_next): ...


class RateLimitMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

        # Config
        self.LOGIN_LIMIT = 5
        self.DEFAULT_LIMIT = 100
        self.WINDOW = 60

    async def dispatch(self, request: Request, call_next):
        # identify client
        ip = request.client.host
        path = request.url.path

        # chose limit
        if path == "/auth/token":
            print("herr")
            limit = self.LOGIN_LIMIT
            key_prefix = "login"
        else:
            limit = self.DEFAULT_LIMIT
            key_prefix = "global"

        # Build key
        key = f"rate_limit{key_prefix}:{ip}"

        # increment counter
        current = await redis_client.incr(key)

        # Set expiry only on first request
        if current == 1:
            await redis_client.expire(key, self.WINDOW)

        # Check limit
        if current > limit:
            ttl = await redis_client.ttl(key)
            return JSONResponse(
                status_code=429,
                content=jsonable_encoder(
                    ErrorResponse(status="error", code=429, message="Too many requests")
                ),
                headers={"Retry-After": str(ttl if ttl > 0 else self.WINDOW)},
            )

        # Continue request
        response = await call_next(request)
        return response
