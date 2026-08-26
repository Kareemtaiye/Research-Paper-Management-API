import ssl
from celery import Celery
from app.core.config import settings

# Determine broker and backend based on environment
if settings.is_production:
    broker_url = settings.prod_celery_broker_url
    backend_url = settings.prod_celery_result_backend
else:
    broker_url = settings.celery_broker_url  # redis://redis:6379/1
    backend_url = settings.celery_result_backend  # redis://redis:6379/2

# SSL only needed for rediss:// (Upstash in production)
use_ssl = (
    {"ssl_cert_reqs": ssl.CERT_NONE} if broker_url.startswith("rediss://") else None
)

celery_app = Celery(
    "research_api",
    broker=broker_url,
    backend=backend_url,
    include=[
        "app.tasks.paper_tasks",
        "app.tasks.email_tasks",
    ],
)

celery_app.conf.update(
    broker_use_ssl=use_ssl,
    redis_backend_use_ssl=use_ssl,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    result_expires=3600,
)
