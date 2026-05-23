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
    """Sync wrapper to to run async arxiv logic."""

    async def run_fetch() -> dict:
        # Fresh connection — owned entirely by this task
        conn = await asyncpg.connect(settings.database_url)

        try:

            """Fetch and store paper metadata from Arxiv API."""  # Update status to processing
            await conn.execute(
                "UPDATE papers SET status = 'processing' WHERE id = $1", paper_id
            )

            # Fetch from Arxiv
            # response = httpx.get(
            #     ARXIV_API, params={"id_list": arxiv_id, "max_results": 1}, timeout=30.0
            # )

            # response.raise_for_status()
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    ARXIV_API,
                    params={"id_list": arxiv_id, "max_results": 1},
                    follow_redirects=True,
                )

            response.raise_for_status()
            # Parse XML — same as your Arxiv fetcher project
            root = ET.fromstring(response.text)
            entry = root.find("atom:entry", NAMESPACE)

            if entry is None:
                await conn.execute(
                    "UPDATE papers SET status = 'failed' WHERE id = $1", paper_id
                )
                logger.error(f"Paper {paper_id} not found on Arxiv with ID {arxiv_id}")
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

            print(
                "fetched data: ",
                {
                    "title": title,
                    "abstract": abstract,
                    "authors": authors,
                    "categories": categories,
                    "published": published,
                },
            )

            published_at = parse_arxiv_datetime(published)

            # Store enriched data
            await conn.execute(
                """
                UPDATE papers
                SET title = $2,
                    abstract = $3, 
                    authors = $4, 
                    categories = $5, 
                    published_at = $6, 
                    status = 'completed',
                    updated_at = NOW()
                WHERE id = $1
                """,
                paper_id,
                title,
                abstract,
                authors,
                categories,
                published_at,
            )

            logger.info(f"Fetched metadata for paper {paper_id} from Arxiv: {title}")

            # Chain email notification
            send_paper_notification.delay(owner_id, paper_id)

            return {"status": "completed", "title": title, "paper_id": paper_id}
        except Exception as exc:
            await conn.execute(
                "UPDATE papers SET status = 'failed' WHERE id = $1", paper_id
            )
            logger.error(
                f"Error fetching metadata for paper {paper_id} from Arxiv: {exc}"
            )
            raise exc
        finally:
            await conn.close()

    try:
        return asyncio.run(run_fetch())
    except httpx.TimeoutException as exc:
        # Retry on timeout
        logger.warning(
            f"Timeout fetching metadata for paper {paper_id} from Arxiv (attempt {self.request.retries + 1}/3)"
        )
        raise self.retry(exc=exc, countdown=2**self.request.retries)  # 1min, 2min, 4min
    except Exception as exc:
        raise self.retry(exc=exc)


@celery_app.task()
def test_task(a, b):
    """A simple test task to verify Celery is working."""
    return f"Task received: {a + b}"
