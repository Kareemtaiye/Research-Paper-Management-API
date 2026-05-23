import psycopg2
import os

DATABASE_URL = os.getenv("DATABASE_URL")


def get_sync_conn():
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
                SELECT id, title, authors, arxiv_url, published_at FROM papers WHERE id = %s
                """,
                (str(paper_id),),
            )
            row = cur.fetchone()
            if row:
                return {
                    "id": str(row[0]),
                    "title": row[1],
                    "authors": row[2],
                    "arxiv_url": row[3],
                    "published_at": row[4],
                }
            return None
    finally:
        conn.close()
