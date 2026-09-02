import asyncpg

from app.core.database import with_connection


class PaperRepository:
    @with_connection
    async def create_paper_entry(self, conn: asyncpg.Connection, data: dict):
        query = """
            INSERT INTO papers (title, owner_id, content)
            VALUES ($1, $2, $3)
            RETURNING *
        """

        return await conn.fetchrow(
            query, data["title"], data["owner_id"], data["content"]
        )

    # ------ v2 features -------
    @with_connection
    async def create_arxiv_paper_entry(self, conn: asyncpg.Connection, data: dict):
        """Arxiv import creates a paper entry with pending status."""

        query = """
            INSERT INTO papers (title, owner_id, arxiv_url, arxiv_id, status, task_id)
            VALUES ($1, $2, $3, $4, 'pending', $5)
            RETURNING *
        """

        return await conn.fetchrow(
            query,
            data["temp_title"],
            data["owner_id"],
            data.get("arxiv_url", ""),
            data.get("arxiv_id", ""),
            data.get("task_id", ""),
        )

    @with_connection
    async def update_paper_task_id(
        self, conn: asyncpg.Connection, paper_id: str, task_id: str
    ):
        query = "UPDATE papers SET task_id = $1 WHERE id = $2"
        status_str = await conn.execute(query, task_id, paper_id)
        operation, _, affected_row = status_str.rpartition(" ")
        return int(affected_row)

    @with_connection
    async def get_paper_by_task_id(self, conn: asyncpg.Connection, task_id: str):
        query = "SELECT id, status, title, arxiv_id FROM papers WHERE task_id = $1"

        return await conn.fetchrow(query, task_id)

    # ------ -------

    @with_connection
    async def get_all_papers(self, conn: asyncpg.Connection, page: int, per_page: int):

        offset = (page - 1) * per_page

        data_query = "SELECT * FROM papers OFFSET $1 LIMIT $2"
        count_query = "SELECT COUNT(*) FROM papers"

        data = await conn.fetch(data_query, offset, per_page)
        count = await conn.fetchval(count_query)
        return {"data": data, "count": count}

    @with_connection
    async def get_paper(self, conn: asyncpg.Connection, paper_id: str):
        query = "SELECT * FROM papers WHERE id = $1"

        return await conn.fetchrow(query, paper_id)

    @with_connection
    async def get_user_papers(
        self, conn: asyncpg.Connection, user_id: str, page: int, per_page: int
    ):
        offset = (page - 1) * per_page

        data_query = " SELECT * FROM papers WHERE owner_id = $1 OFFSET $2 LIMIT $3"
        count_query = "SELECT COUNT(*) FROM papers WHERE owner_id = $1"

        data = await conn.fetch(data_query, user_id, offset, per_page)
        count = await conn.fetchval(count_query, user_id)
        return {"data": data, "count": count}

    @with_connection
    async def delete_paper(self, conn: asyncpg.Connection, paper_id: str):
        """Returns the number of deleted row - 0 if no row was deleted"""
        query = "DELETE FROM papers WHERE id = $1"

        status_str = await conn.execute(query, paper_id)
        operation, _, affected_row = status_str.rpartition(" ")
        return int(affected_row)

    @with_connection
    async def update_paper_status(
        self, conn: asyncpg.Connection, paper_id: str, status_str: str
    ):
        query = "UPDATE papers SET status = $1 WHERE id = $2"

        status_str = await conn.execute(query, status_str, paper_id)
        operation, _, affected_row = status_str.rpartition(" ")
        return int(affected_row)

    @with_connection
    async def update_paper_metadata(
        self,
        conn: asyncpg.Connection,
        paper_id: str,
        title: str,
        abstract: str,
        authors: list[str],
        categories: str,
        published_at: str,
        status: str,
    ):
        query = """
        UPDATE papers 
        SET title = $1
            abstract = $2
            authors = $3
            categories = $4
            published_at = $5
            status = $6
        WHERE id = $7
        """
        status_str = await conn.ececute(
            query,
            title,
            abstract,
            authors,
            categories,
            published_at,
            status,
            paper_id,
        )

        operation, _, affected_row = status_str.rpartition(" ")
        return int(affected_row)

    @with_connection
    async def get_recent_papers(
        self, conn: asyncpg.Connection, user_id: str, page: int, per_page: int
    ):
        offset = (page - 1) * per_page

        data_query = "SELECT * FROM papers WHERE owner_id = $1 ORDER BY created_at DESC OFFSET $2 LIMIT $3"
        count_query = "SELECT COUNT(*) FROM papers"

        data = await conn.fetch(data_query, user_id, offset, per_page)
        count = await conn.fetchval(count_query)
        return {"data": data, "count": count}

    @with_connection
    async def search_paper(
        self, conn: asyncpg.Connection, q: str, user_id: str, limit: int, offset: int
    ):

        data = await conn.fetch(
            """
        SELECT
           p.id,
            p.title,
            p.arxiv_id,
            p.arxiv_url,
            p.authors,
            p.categories,
            p.abstract,
            p.status,
            p.published_at,
            p.created_at,
            ts_rank(p.search_vector, query) AS rank,
            ts_headline(
                'english',
                COALESCE(p.title, ''),
                query,
                'StartSel=<mark>, StopSel=</mark>, MaxWords=10, MinWords=5'
            ) AS title_headline,
            ts_headline(
                'english',
                COALESCE(p.abstract, ''),
                query,
                'StartSel=<mark>, StopSel=</mark>, MaxFragments=1, MaxWords=20'
            ) AS abstract_headline
        FROM papers p,
             plainto_tsquery('english', $1) query
        WHERE p.owner_id = $2
          AND p.status = 'completed'
          AND p.search_vector @@ query
        ORDER BY rank DESC
        LIMIT $3 OFFSET $4
             """,
            q,
            str(user_id),
            limit,
            offset,
        )

        count = await conn.fetchval(
            """
            SELECT COUNT(*)
            FROM papers p,
                plainto_tsquery('english', $1) query
            WHERE p.owner_id = $2
            AND p.status = 'completed'
            AND p.search_vector @@ query
        """,
            q,
            str(user_id),
        )

        print(f'Search results: {{"data": {data}, "count": {count}}}')

        return {"data": data, "count": count}
