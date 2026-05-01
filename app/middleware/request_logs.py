import time

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logger import logger


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(self, app):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        # request info
        method = request.method
        path = request.url.path
        client_ip = request.client.host

        try:
            response = await call_next(request)
            status_code = response.status_code
        except Exception as e:
            status_code = 500
            logger.exception(f"{client_ip} | {method} | {path} | ERROR")
            raise e

        # calculate duration
        duration = (time.time() - start_time) * 1000  # ms

        # log line
        logger.info(
            f"{client_ip} | {method} | {path} | {status_code} | {duration:.2f}ms"
        )

        return response
