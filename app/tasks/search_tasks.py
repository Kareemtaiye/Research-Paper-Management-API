from app.tasks.celery_app import celery_app
from app.tasks.db_helpers import get_paper_by_id
import asyncio
from app.services.search_service import index_paper, delete_paper


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def sync_paper_to_elasticsearch(self, paper_id: str):
    """Sync a paper from PostgreSQL to Elasticsearch."""
    try:
        paper = get_paper_by_id(paper_id)
        if not paper:
            return {"error": "Paper not found"}

        asyncio.run(index_paper(paper))
        return {"status": "synced", "paper_id": paper_id}

    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def remove_paper_from_elasticsearch(self, paper_id: str):
    """Remove a paper from Elasticsearch when deleted from PostgreSQL."""
    try:
        asyncio.run(delete_paper(paper_id))
        return {"status": "removed", "paper_id": paper_id}

    except Exception as exc:
        raise self.retry(exc=exc)
