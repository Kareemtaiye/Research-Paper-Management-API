from celery import Celery
from app.core.config import settings

# celery_app = Celery("research_api", broker=settings.redis_url)


celery_app = Celery(
    "research_api",
    broker=settings.celery_broker_url,  # Redis receives the tasks
    backend=settings.celery_result_backend,  # Redis stores the results
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
