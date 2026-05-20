# app/tasks/paper_tasks.py
import asyncio

import httpx
import xml.etree.ElementTree as ET
from app.core.database import get_conn
from app.services.paper_service import PaperService
from app.tasks.celery_app import celery_app

service = PaperService()
conn = get_conn()

ARXIV_API = "http://export.arxiv.org/api/query"

NAMESPACE = {"atom": "http://www.w3.org/2005/Atom"}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=60)
def fetch_arxiv_paper_metadata(self, paper_id: str, arxiv_id: str):
    """Sync wrapper to to run async arxiv logic."""

    async def run_fetch() -> dict:
        """Fetch and store paper metadata from Arxiv API."""  # Update status to processing
        await service.update_paper_status(conn, paper_id, "processing")

        # Fetch from Arxiv
        response = httpx.get(
            ARXIV_API, params={"id_list": arxiv_id, "max_results": 1}, timeout=30.0
        )

        response.raise_for_status()

        # Parse XML — same as your Arxiv fetcher project
        root = ET.fromstring(response.text)
        entry = root.find("atom:entry", NAMESPACE)

        if entry is None:
            await service.update_paper_status(conn, paper_id, "failed")
            return {"error": "Paper not found on Arxiv"}

        # Extract fields
        title = entry.find("atom:title", NAMESPACE).text.strip()
        abstract = entry.find("atom:summary", NAMESPACE).text.strip()
        published: str = entry.find("atom:published", NAMESPACE).text

        authors: list[str] = [
            author.find("atom:name", NAMESPACE).text
            for author in entry.findall("atom:author", NAMESPACE)
        ]

        categories: list[str] = [
            cat.get("term")
            for cat in entry.findall(
                "{http://arxiv.org/schemas/atom}category", NAMESPACE
            )
        ]

        # Store enriched data
        await service.update_paper_metadata(
            conn=conn,
            paper_id=paper_id,
            title=title,
            abstract=abstract,
            authors=authors,
            categories=categories,
            published_at=published,
            status="completed",
        )

        return {"status": "completed", "title": title, "paper_id": paper_id}

    try:
        return asyncio.run(run_fetch())
    except httpx.TimeoutException as exc:
        # Retry on timeout
        raise self.retry(exc=exc, countdown=2**self.request.retries)  # 1min, 2min, 4min
    except Exception as exc:
        asyncio.run(service.update_paper_status(conn, paper_id, "failed"))
        raise self.retry(exc=exc)


@celery_app.task()
def test_task(a, b):
    """A simple test task to verify Celery is working."""
    return f"Task received: {a + b}"
