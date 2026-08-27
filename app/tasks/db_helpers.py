import json

import psycopg2
from app.core.config import settings

DATABASE_URL = (
    settings.prod_database_url if settings.is_production else settings.database_url
)


def get_sync_conn():
    # Only use SSL in production
    if settings.is_production:
        return psycopg2.connect(DATABASE_URL, sslmode="require")
    else:
        return psycopg2.connect(DATABASE_URL)


def get_user_by_id(user_id: str):
    conn = get_sync_conn()

    try:
        with conn.cursor() as cur:
            cur.execute("SELECT id, email FROM users WHERE id = %s", (str(user_id),))
            row = cur.fetchone()
            if row:
                return {"id": str(row[0]), "email": row[1]}
            return None
    finally:
        conn.close()


def get_paper_by_id(paper_id: str):
    conn = get_sync_conn()

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, owner_id, title, authors, arxiv_url, categories, abstract, published_at FROM papers WHERE id = %s
                """,
                (str(paper_id),),
            )
            row = cur.fetchone()
            if row:
                return {
                    "id": str(row[0]),
                    "owner_id": str(row[1]),
                    "title": row[2],
                    "authors": row[3],
                    "arxiv_url": row[4],
                    "categories": row[5],
                    "abstract": row[6],
                    "published_at": row[7],
                }
            return None
    finally:
        conn.close()


# app/tasks/db_helpers.py


def create_task_record(task_id: str, owner_id: str, task_type: str, paper_id: str):
    conn = get_sync_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tasks (task_id, owner_id, task_type, paper_id, status)
                VALUES (%s, %s, %s, %s, 'pending')
                RETURNING id
            """,
                (task_id, owner_id, task_type, paper_id),
            )
        conn.commit()
    finally:
        conn.close()


def update_task_record(
    task_id: str,
    status: str,
    progress: int | None = None,
    stage: str | None = None,
    stage_message: str | None = None,
    result: dict | None = None,
    error: str | None = None,
    worker_name: str | None = None,
):

    conn = get_sync_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE tasks SET
                    status = %s,
                    progress = COALESCE(%s, progress),
                    stage = COALESCE(%s, stage),
                    stage_message = COALESCE(%s, stage_message),
                    result = COALESCE(%s, result),
                    error = COALESCE(%s, error),
                    completed_at = CASE 
                        WHEN %s IN ('completed','failed') THEN NOW() 
                        ELSE completed_at 
                    END,
                    worker_name = COALESCE(%s, worker_name),
                    updated_at = NOW()
                WHERE task_id = %s
            """,
                (
                    status,
                    progress,
                    stage,
                    stage_message,
                    json.dumps(result) if result else None,
                    error,
                    status,
                    worker_name,
                    task_id,
                ),
            )
        conn.commit()
    finally:
        conn.close()


def _update_status_sync(paper_id: str, status: str):
    conn = get_sync_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE papers SET status = %s, updated_at = NOW() WHERE id = %s",
                (status, paper_id),
            )
        conn.commit()
    finally:
        conn.close()


def update_real_task_id(placeholder_id: str, real_task_id: str):
    """Replace placeholder task_id with real Celery task_id."""
    conn = get_sync_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE tasks SET task_id = %s WHERE task_id = %s",
                (real_task_id, placeholder_id),
            )
        conn.commit()
    finally:
        conn.close()
