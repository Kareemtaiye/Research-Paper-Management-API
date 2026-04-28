import asyncpg

from app.core.database import with_connection


class PaperTagRepository:
    @with_connection
    async def create_paper_tag(
        self, conn: asyncpg.Connection, paper_id: str, tag_id: str
    ):
        query = """
            INSERT INTO paper_tags (paper_id, tag_id)
            VALUES ($1, $2)
            RETURNING id
        """

        return await conn.fetchrow(query, paper_id, tag_id)

    @with_connection
    async def get_all_paper_tag(
        self, conn: asyncpg.Connection, page: int, per_page: int
    ):

        offset = (page - 1) * per_page
        data_query = "SELECT * FROM paper_tags OFFSET $1 LIMIT $2"
        count_query = "SELECT COUNT(*) FROM paper_tags"

        data = await conn.fetch(data_query, offset, per_page)
        count = await conn.fetchval(count_query)
        return {"data": data, "count": count}
