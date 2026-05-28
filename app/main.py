from fastapi import FastAPI
from app.core.database import lifespan
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_logs import (
    # RequestLoggingMiddleware,
    add_logger_middleware,
)
from app.routers import auth, papers_import, task, user, paper, tag, websocket, search
from app.exceptions.handlers import register_exception_handlers
from app.services.search_service import create_index_if_not_exists
from app.tasks.paper_tasks import test_task
from prometheus_fastapi_instrumentator import Instrumentator

app = FastAPI(lifespan=lifespan)
Instrumentator().instrument(app).expose(app)


@app.get("/health", tags=["Health"])
def check_health():

    return {
        "status": "Ok",
        "test_task": "active" if test_task(10, 20) == 30 else "non-actuve",
    }


# cos gastapi wont call the handlers unless thy're registered or imported in this modile
register_exception_handlers(app)
app.add_middleware(RateLimitMiddleware)
# app.add_middleware(RequestLoggingMiddleware)
add_logger_middleware(app)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(user.router, prefix="/api/v1")
app.include_router(search.router, prefix="/api/v1")
app.include_router(paper.router, prefix="/api/v1")
app.include_router(papers_import.router, prefix="/api/v1")
app.include_router(tag.router, prefix="/api/v1")
app.include_router(task.router, prefix="/api/v1")
app.include_router(websocket.router, prefix="/api/v1")


@app.get("/", tags=["index"])
def home():
    return "Welcome to the research management api server"
