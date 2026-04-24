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

    @with_connection
    async def get_all_papers(self, conn: asyncpg.Connection, page, per_page):

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
        self, conn: asyncpg.Connection, user_id: str, page, per_page
    ):
        offset = (page - 1) * per_page

        data_query = " SELECT * FROM papers WHERE owner_id = $1 OFFSET $2 LIMIT $3"
        count_query = "SELECT COUNT(*) FROM papers"

        data = await conn.fetch(data_query, user_id, offset, per_page)
        count = await conn.fetchval(count_query)

        return {"data": data, "count": count}

    @with_connection
    async def delete_paper(self, conn: asyncpg.Connection, paper_id: str):
        """Returns the number of deleted row - 0 if no row was deleted"""
        query = "DELETE FROM papers WHERE id = $1"

        status_str = await conn.execute(query, paper_id)
        operation, _, affected_row = status_str.rpartition(" ")

        return int(affected_row)
