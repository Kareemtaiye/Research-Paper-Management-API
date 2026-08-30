# app/tasks/paper_tasks.py
from datetime import date, datetime
import httpx
import xml.etree.ElementTree as ET
from app.tasks.celery_app import celery_app
from app.core.config import settings
from app.core.logger import logger
from app.tasks.email_tasks import send_paper_notification
from app.services.pubsub import publish_sync
from app.tasks.db_helpers import (
    get_sync_conn,
    _update_status_sync,
    update_task_record,
)

DB_URL = settings.prod_database_url if settings.is_production else settings.database_url

ARXIV_API = "https://export.arxiv.org/api/query"
NAMESPACE = {"atom": "http://www.w3.org/2005/Atom"}


def parse_arxiv_datetime(val: str | date | datetime) -> datetime:
    if isinstance(val, datetime):
        return val.replace(tzinfo=None)
    if isinstance(val, date):
        return datetime.combine(val, datetime.min.time())
    return datetime.fromisoformat(val.replace("Z", "+00:00")).replace(tzinfo=None)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_arxiv_paper_metadata(self, paper_id: str, arxiv_id: str, owner_id: str):

    # Stage 1 — worker picked up task
    update_task_record(
        self.request.id,
        status="processing",
        progress=0,
        stage="starting",
        stage_message="Fetching from Arxiv...",
        worker_name=self.request.hostname,
    )

    try:
        # Stage 2 — calling Arxiv API
        update_task_record(
            self.request.id,
            status="processing",
            progress=25,
            stage="fetching_metadata",
            stage_message="Calling Arxiv API…",
        )

        with httpx.Client(timeout=30.0) as client:
            response = client.get(
                ARXIV_API,
                params={"id_list": arxiv_id, "max_results": 1},
                follow_redirects=True,
            )
        response.raise_for_status()

        # Stage 3 — parsing response
        update_task_record(
            self.request.id,
            status="processing",
            progress=50,
            stage="parsing",
            stage_message="Parsing paper metadata…",
        )

        root = ET.fromstring(response.text)
        entry = root.find("atom:entry", NAMESPACE)

        if entry is None:
            _update_status_sync(str(paper_id), "failed")
            update_task_record(
                self.request.id,
                status="failed",
                progress=0,
                stage="failed",
                stage_message="Paper not found on Arxiv",
                error="Paper not found on Arxiv",
            )
            publish_sync(
                owner_id,
                {
                    "event": "paper_failed",
                    "paper_id": str(paper_id),
                    "status": "failed",
                    "message": "Paper not found on Arxiv",
                },
            )
            return {"error": "Paper not found on Arxiv"}

        title = entry.find("atom:title", NAMESPACE).text.strip()
        abstract = entry.find("atom:summary", NAMESPACE).text.strip()
        published = entry.find("atom:published", NAMESPACE).text
        authors = [
            author.find("atom:name", NAMESPACE).text
            for author in entry.findall("atom:author", NAMESPACE)
        ]
        categories = list(
            set(
                [
                    cat.get("term")
                    for cat in entry.findall("atom:category", NAMESPACE)
                    if cat.get("term")
                ]
            )
        )
        published_at = parse_arxiv_datetime(published)

        # Stage 4 — saving to database
        update_task_record(
            self.request.id,
            status="processing",
            progress=75,
            stage="saving",
            stage_message="Saving to database…",
        )

        conn = get_sync_conn()
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    UPDATE papers
                    SET title = %s, abstract = %s, authors = %s,
                        categories = %s, published_at = %s,
                        status = 'completed', updated_at = NOW()
                    WHERE id = %s
                    """,
                    (title, abstract, authors, categories, published_at, str(paper_id)),
                )
            conn.commit()
        finally:
            conn.close()

        logger.info(f"Fetched metadata for paper {paper_id}: {title}")

        # Stage 5 — complete
        update_task_record(
            self.request.id,
            status="completed",
            progress=100,
            stage="completed",
            stage_message="Import complete",
            result={"paper_id": str(paper_id), "title": title},
        )

        # Notify client via WebSocket
        publish_sync(
            owner_id,
            {
                "event": "paper_completed",
                "paper_id": str(paper_id),
                "title": title,
                "status": "completed",
            },
        )

        # Queue email notification
        send_paper_notification.delay(owner_id, paper_id)

        return {"status": "completed", "title": title, "paper_id": paper_id}

    except httpx.TimeoutException as exc:
        retry_num = self.request.retries + 1
        wait = 2**self.request.retries

        if retry_num >= self.max_retries:
            update_task_record(
                self.request.id,
                status="failed",
                stage="failed",
                stage_message="Arxiv API timed out after 3 attempts",
                error="Connection timeout — Arxiv API unreachable",
            )
            _update_status_sync(str(paper_id), "failed")
            publish_sync(
                owner_id,
                {
                    "event": "paper_failed",
                    "paper_id": str(paper_id),
                    "status": "failed",
                    "message": "Import failed — Arxiv API unreachable after 3 attempts",
                },
            )
            return

        _update_status_sync(str(paper_id), "retrying")
        publish_sync(
            owner_id,
            {
                "event": "paper_retrying",
                "paper_id": str(paper_id),
                "status": "retrying",
                "attempt": retry_num,
                "max_attempts": 3,
                "retry_in": wait,
                "message": f"Attempt {retry_num}/3 failed — retrying in {wait}s",
            },
        )
        update_task_record(
            self.request.id,
            status="processing",
            stage="retrying",
            stage_message=f"Arxiv timed out — retrying in {wait}s (attempt {retry_num}/3)…",
        )
        logger.warning(f"Timeout fetching paper {paper_id} (attempt {retry_num}/3)")
        raise self.retry(exc=exc, countdown=wait)

    except httpx.HTTPStatusError as exc:
        retry_num = self.request.retries + 1
        status_code = exc.response.status_code
        wait = 2**self.request.retries

        if status_code == 429:
            if retry_num > self.max_retries:
                update_task_record(
                    self.request.id,
                    status="failed",
                    stage="failed",
                    stage_message="Rate limited by Arxiv after 3 attempts",
                    error="429 Too Many Requests",
                )
                _update_status_sync(str(paper_id), "failed")
                return
            update_task_record(
                self.request.id,
                status="processing",
                stage="retrying",
                stage_message=f"Rate limited by Arxiv — retrying in {wait * 60}s (attempt {retry_num}/3)…",
            )
            raise self.retry(exc=exc, countdown=wait * 60)

        if status_code == 404:
            update_task_record(
                self.request.id,
                status="failed",
                stage="failed",
                stage_message=f"Paper {arxiv_id} not found on Arxiv",
                error="404 Not Found — invalid Arxiv ID",
            )
            _update_status_sync(str(paper_id), "failed")
            publish_sync(
                owner_id,
                {
                    "event": "paper_failed",
                    "paper_id": str(paper_id),
                    "status": "failed",
                    "message": f"Paper {arxiv_id} not found on Arxiv",
                },
            )
            return

        if status_code >= 500:
            if retry_num > self.max_retries:
                update_task_record(
                    self.request.id,
                    status="failed",
                    stage="failed",
                    stage_message=f"Arxiv server error after 3 attempts ({status_code})",
                    error=f"HTTP {status_code} Server Error",
                )
                _update_status_sync(str(paper_id), "failed")
                return
            update_task_record(
                self.request.id,
                status="processing",
                stage="retrying",
                stage_message=f"Arxiv server error — retrying in {wait * 60}s (attempt {retry_num}/3)…",
            )
            raise self.retry(exc=exc, countdown=wait * 60)

        update_task_record(
            self.request.id,
            status="failed",
            stage="failed",
            stage_message=f"Unexpected HTTP error: {status_code}",
            error=str(exc),
        )
        _update_status_sync(str(paper_id), "failed")
        publish_sync(
            owner_id,
            {
                "event": "paper_failed",
                "paper_id": str(paper_id),
                "status": "failed",
                "message": f"HTTP error: {status_code}",
            },
        )
        return

    except Exception as exc:
        retry_num = self.request.retries + 1

        _update_status_sync(str(paper_id), "retrying")
        publish_sync(
            owner_id,
            {
                "event": "paper_retrying",
                "paper_id": str(paper_id),
                "status": "retrying",
                "attempt": retry_num,
                "max_attempts": 3,
                "retry_in": 60,
                "message": f"Attempt {retry_num}/3 failed — retrying in 60s",
            },
        )

        if self.request.retries >= self.max_retries - 1:
            update_task_record(
                self.request.id,
                status="failed",
                stage="failed",
                stage_message="Unexpected error — all retries exhausted",
                error=str(exc),
            )
            _update_status_sync(str(paper_id), "failed")
            publish_sync(
                owner_id,
                {
                    "event": "paper_failed",
                    "paper_id": str(paper_id),
                    "status": "failed",
                    "message": "Import failed after 3 attempts",
                },
            )
            return

        update_task_record(
            self.request.id,
            status="processing",
            stage="retrying",
            stage_message=f"Unexpected error — retrying (attempt {retry_num}/3)…",
            error=str(exc),
        )

        logger.error(f"Unexpected error fetching paper {paper_id}: {exc}")
        raise self.retry(exc=exc)


@celery_app.task()
def test_task(a, b):
    """A simple test task to verify Celery is working."""
    return f"Task received: {a + b}"
