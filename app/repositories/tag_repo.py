import asyncpg

from app.core.database import with_connection


class TagRepository:
    @with_connection
    async def get_all_tags(self, conn: asyncpg.Connection, page: int, per_page: int):
        offset = (page - 1) * per_page
        data_query = "SELECT * FROM tags OFFSET $1 LIMIT $2"
        count_query = "SELECT COUNT(*) FROM tags"

        data = await conn.fetch(data_query, offset, per_page)
        count = await conn.fetchval(count_query)
        return {"data": data, "count": count}
