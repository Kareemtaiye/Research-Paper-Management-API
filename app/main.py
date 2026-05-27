from fastapi import FastAPI
from app.core.database import lifespan
from app.middleware.rate_limit import RateLimitMiddleware
from app.middleware.request_logs import (
    # RequestLoggingMiddleware,
    add_logger_middleware,
)
from app.routers import auth, papers_import, task, user, paper, tag, websocket
from app.exceptions.handlers import register_exception_handlers
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

app.include_router(auth.router)
app.include_router(user.router)
app.include_router(paper.router)
app.include_router(papers_import.router)
app.include_router(tag.router)
app.include_router(task.router)
app.include_router(websocket.router)


@app.get("/", tags=["index"])
def home():
    return "Welcome to the research management api server"
