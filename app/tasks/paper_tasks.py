# app/tasks/paper_tasks.py
import asyncio
from datetime import date, datetime
import asyncpg
import httpx
import xml.etree.ElementTree as ET
from app.tasks.celery_app import celery_app
from app.core.config import settings
from app.core.logger import logger
from app.tasks.email_tasks import send_paper_notification
from app.services.pubsub import publish_sync
from app.tasks.db_helpers import _update_status_sync, update_task_record

# from app.tasks.search_tasks import sync_paper_to_elasticsearch

# # Syncing to search
# update_task_record(
#     self.request.id,
#     status="processing",
#     progress=90,
#     stage="syncing",
#     stage_message="Syncing to Elasticsearch…"
# )

DB_URL = settings.prod_database_url if settings.is_production else settings.database_url


def parse_arxiv_datetime(val: str | date | datetime) -> datetime:
    if isinstance(val, datetime):
        return val.replace(tzinfo=None)

    if isinstance(val, date):
        return datetime.combine(val, datetime.min.time())

    return datetime.fromisoformat(val.replace("Z", "+00:00")).replace(tzinfo=None)


# service = PaperService()
# conn = get_conn()

ARXIV_API = "https://export.arxiv.org/api/query"

NAMESPACE = {"atom": "http://www.w3.org/2005/Atom"}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_arxiv_paper_metadata(self, paper_id: str, arxiv_id: str, owner_id: str):
    # First thing — update to processing
    update_task_record(
        self.request.id,
        status="processing",
        progress=0,
        stage="fetching_metadata",
        stage_message="Fetching from Arxiv...",
        worker_name=self.request.hostname,
    )

    async def run_fetch() -> dict:
        conn = await asyncpg.connect(DB_URL)
        try:
            await conn.execute(
                "UPDATE papers SET status = 'processing' WHERE id = $1", paper_id
            )

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    ARXIV_API,
                    params={"id_list": arxiv_id, "max_results": 1},
                    follow_redirects=True,
                )
            response.raise_for_status()

            root = ET.fromstring(response.text)
            entry = root.find("atom:entry", NAMESPACE)

            if entry is None:
                await conn.execute(
                    "UPDATE papers SET status = 'failed' WHERE id = $1", paper_id
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
                        for cat in entry.findall(
                            "atom:category", {"atom": "http://www.w3.org/2005/Atom"}
                        )
                        if cat.get("term")
                    ]
                )
            )
            published_at = parse_arxiv_datetime(published)

            await conn.execute(
                """
                UPDATE papers
                SET title = $2, abstract = $3, authors = $4,
                    categories = $5, published_at = $6,
                    status = 'completed', updated_at = NOW()
                WHERE id = $1
            """,
                paper_id,
                title,
                abstract,
                authors,
                categories,
                published_at,
            )

            logger.info(f"Fetched metadata for paper {paper_id}: {title}")
            return {"status": "completed", "title": title, "paper_id": paper_id}

        except Exception as exc:
            await conn.execute(
                "UPDATE papers SET status = 'failed' WHERE id = $1", paper_id
            )
            logger.error(f"Error fetching metadata for paper {paper_id}: {exc}")
            raise exc
        finally:
            await conn.close()

    # Sync layer
    try:
        # Step 2 — fetch is happening
        update_task_record(
            self.request.id,
            status="processing",
            progress=25,
            stage="fetching_metadata",
            stage_message="Calling Arxiv API…",
        )

        result = asyncio.run(run_fetch())

        # Step 3 — fetch done, check result
        if result.get("error"):
            update_task_record(
                self.request.id,
                status="failed",
                progress=0,
                stage="failed",
                stage_message=result["error"],
                error=result["error"],
            )
            return result

        # Step 4 — parsing done (happened inside run_fetch)
        update_task_record(
            self.request.id,
            status="processing",
            progress=60,
            stage="parsing",
            stage_message="Parsing paper metadata…",
        )

        # Saving to DB
        update_task_record(
            self.request.id,
            status="processing",
            progress=70,
            stage="saving",
            stage_message="Saving to database…",
        )

        if result.get("status") == "completed":
            # Publish AFTER asyncio.run() — clean event loop
            publish_sync(
                owner_id,
                {
                    "event": "paper_completed",
                    "paper_id": str(paper_id),
                    "title": result["title"],
                    "status": "completed",
                },
            )
        # Step 7 — queue email
        send_paper_notification.delay(owner_id, paper_id)

        # Step 8 — mark task as completed
        update_task_record(
            self.request.id,
            status="completed",
            progress=100,
            stage="completed",
            stage_message="Import complete",
            result={"paper_id": str(paper_id), "title": result["title"]},
        )

        return result

    except httpx.TimeoutException as exc:
        retry_num = self.request.retries + 1
        wait = 2**self.request.retries  # 1min, 2min, 4min

        if retry_num >= self.max_retries:
            update_task_record(
                self.request.id,
                status="failed",
                stage="failed",
                stage_message="Arxiv API timed out after 3 attempts",
                error="Connection timeout — Arxiv API unreachable",
            )

        # Update status to retrying before retry
        _update_status_sync(paper_id, "retrying")
        publish_sync(
            owner_id,
            {
                "event": "paper_retrying",
                "paper_id": str(paper_id),
                "status": "retrying",
                "attempt": self.request.retries + 1,
                "max_attempts": 3,
                "retry_in": 2**self.request.retries,
                "message": f"Attempt {self.request.retries + 1}/3 failed — retrying in {2 ** self.request.retries}s",
            },
        )

        update_task_record(
            self.request.id,
            status="processing",
            stage="retrying",
            stage_message=f"Arxiv timed out — retrying in {wait}m (attempt {retry_num}/3)…",
        )

        logger.warning(
            f"Timeout fetching paper {paper_id} (attempt {self.request.retries + 1}/3)"
        )
        raise self.retry(exc=exc, countdown=2**self.request.retries)

    except httpx.HTTPStatusError as exc:
        retry_num = self.request.retries + 1
        status_code = exc.response.status_code

        # 429 rate limited
        if status_code == 429:
            if retry_num > self.max_retries:
                update_task_record(
                    self.request.id,
                    status="failed",
                    stage="failed",
                    stage_message="Rate limited by Arxiv after 3 attempts",
                    error="429 Too Many Requests",
                )
                _update_status_sync(paper_id, "failed")
                return

            update_task_record(
                self.request.id,
                status="processing",
                stage="retrying",
                stage_message=f"Rate limited by Arxiv — retrying in {wait}m (attempt {retry_num}/3)…",
            )
            raise self.retry(exc=exc, countdown=wait * 60)

        # 404 paper not found — no point retrying
        if status_code == 404:
            update_task_record(
                self.request.id,
                status="failed",
                stage="failed",
                stage_message=f"Paper {arxiv_id} not found on Arxiv",
                error="404 Not Found — invalid Arxiv ID",
            )
            _update_status_sync(paper_id, "failed")
            return

        # 5xx server error — retry
        if status_code >= 500:
            if retry_num > self.max_retries:
                update_task_record(
                    self.request.id,
                    status="failed",
                    stage="failed",
                    stage_message=f"Arxiv server error after 3 attempts ({status_code})",
                    error=f"HTTP {status_code} Server Error",
                )
                _update_status_sync(paper_id, "failed")
                return

            update_task_record(
                self.request.id,
                status="processing",
                stage="retrying",
                stage_message=f"Arxiv server error — retrying in {wait}m (attempt {retry_num}/3)…",
            )
            raise self.retry(exc=exc, countdown=wait * 60)

        # anything else — fail immediately
        update_task_record(
            self.request.id,
            status="failed",
            stage="failed",
            stage_message=f"Unexpected HTTP error: {status_code}",
            error=str(exc),
        )
        _update_status_sync(paper_id, "failed")
        return

    except Exception as exc:
        if not self.request.retries < self.max_retries:
            update_task_record(
                self.request.id,
                status="failed",
                stage="failed",
                stage_message="Unexpected error — all retries exhausted",
                error=str(exc),
            )

        _update_status_sync(paper_id, "retrying")
        publish_sync(
            owner_id,
            {
                "event": "paper_retrying",
                "paper_id": str(paper_id),
                "status": "retrying",
                "attempt": self.request.retries + 1,
                "max_attempts": 3,
                "retry_in": 60,
                "message": f"Attempt {self.request.retries + 1}/3 failed — retrying in 60s",
            },
        )

        # If all retries exhausted — mark as permanently failed
        if self.request.retries >= self.max_retries - 1:
            _update_status_sync(paper_id, "failed")
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

        raise self.retry(exc=exc)


@celery_app.task()
def test_task(a, b):
    """A simple test task to verify Celery is working."""
    return f"Task received: {a + b}"
