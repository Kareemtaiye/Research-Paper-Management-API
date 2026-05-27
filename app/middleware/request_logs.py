import time
from fastapi import FastAPI, Request
from app.core.logger import logger

# ---- v1 -----
# class RequestLoggingMiddleware(BaseHTTPMiddleware):
#     def __init__(self, app):
#         super().__init__(app)

#     async def dispatch(self, request: Request, call_next):
#         start_time = time.time()

#         # request info
#         client_ip = request.client.host

#         # Check for X-Forwarded-For header
#         forwarded = request.headers.get("X-Forwarded-For")
#         if forwarded:
#             # Get the first IP in the comma-separated list
#             ip = forwarded.split(",")[0].strip()

#         method = request.method
#         path = request.url.path

#         try:
#             response = await call_next(request)
#             status_code = response.status_code
#         except Exception as e:
#             status_code = 500
#             logger.exception(f"{client_ip} | {method} | {path} | ERROR")
#             raise e

#         # calculate duration
#         duration = (time.time() - start_time) * 1000  # ms

#         # log line
#         logger.info(
#             f"{client_ip} | {method} | {path} | {status_code} | {duration:.2f}ms"
#         )

#         return response


def add_logger_middleware(app: FastAPI):
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        start_time = time.time()
        correlation_id = request.headers.get("X-Correlation-ID", "unknown")

        # Resolve the real client ip addr
        forwarded = request.headers.get("X-Forwarded-For")
        client_ip = (
            forwarded.split(",")[0].strip()
            if forwarded
            else (request.client.host if request.client else "unknown")
        )

        # Context dict for logging
        log_context = {
            "correlation_id": correlation_id,
            "client_ip": client_ip,
            "method": request.method,
            "path": request.url.path,
        }

        try:
            logger.info("request started", extra=log_context)

            response = await call_next(request)

            duration_ms = (time.time() - start_time) * 1000

            log_context.update(
                {
                    "status_code": response.status_code,
                    "duration_ms": round(duration_ms, 2),
                }
            )

            logger.info("request completed", extra=log_context)

            return response
        except Exception as e:
            # Handle unhandled system crashes cleanly without duplicate traceback logs
            duration_ms = (time.time() - start_time) * 1000
            log_context.update(
                {"status_code": 500, "duration_ms": round(duration_ms, 2)}
            )

            logger.error(
                f"{client_ip} | {request.method} | {request.url.path} | 500 | {duration_ms:.2f}ms | ERROR: {str(e)}",
                extra=log_context,
            )
            raise e
