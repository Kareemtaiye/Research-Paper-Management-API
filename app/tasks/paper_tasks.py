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
from app.tasks.db_helpers import _update_status_sync

# from app.tasks.search_tasks import sync_paper_to_elasticsearch

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

    # ── Sync layer ─────────────────────────────────────────────
    try:
        result = asyncio.run(run_fetch())

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
            send_paper_notification.delay(owner_id, paper_id)

        return result

    except httpx.TimeoutException as exc:
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

        logger.warning(
            f"Timeout fetching paper {paper_id} (attempt {self.request.retries + 1}/3)"
        )
        raise self.retry(exc=exc, countdown=2**self.request.retries)
    except Exception as exc:

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
