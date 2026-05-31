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

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,  # task shows "started" not just "pending"
    result_expires=3600,  # results stored in Redis for 1 hour
)
