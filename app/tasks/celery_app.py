import os
import ssl
from celery import Celery
from app.core.config import settings

# celery_app = Celery("research_api", broker=settings.redis_url)


celery_app = Celery(
    "research_api",
    broker=(
        settings.prod_celery_broker_url  # Receives the task
        if settings.is_production
        else settings.celery_broker_url
    ),
    backend=(
        settings.prod_celery_result_backend  # Stores the result of the task
        if settings.is_production
        else settings.celery_result_backend
    ),
    include=[
        "app.tasks.paper_tasks",
        "app.tasks.email_tasks",
        # "app.tasks.export_tasks",
    ],
)

# 1. Get the current broker URL from the environment string
broker_url = os.environ.get("CELERY_BROKER_URL", "")

# 2. Dynamically determine if SSL options are needed based on the URL scheme
# (Only apply SSL parameters if the URL explicitly starts with rediss://)
use_ssl = (
    {"ssl_cert_reqs": ssl.CERT_NONE} if broker_url.startswith("rediss://") else None
)


celery_app.conf.update(
    broker_use_ssl=use_ssl,
    redis_backend_use_ssl=use_ssl,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,  # task shows "started" not just "pending"
    result_expires=3600,  # results stored in Redis for 1 hour
)
