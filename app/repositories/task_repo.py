import asyncpg
from app.core.database import with_connection


class TaskRepository:
    @with_connection
    async def get_all_tasks(
        self, conn: asyncpg.Connection, user_id: str, page: int = 1, per_page: int = 10
    ):

        offset = (page - 1) * per_page

        data_query = "SELECT * FROM tasks WHERE owner_id = $3 OFFSET $1 LIMIT $2"
        count_query = "SELECT COUNT(*) FROM tasks WHERE owner_id = $1"

        data = await conn.fetch(data_query, offset, per_page, user_id)
        count = await conn.fetchval(count_query, user_id)
        return {"data": data, "count": count}

    @with_connection
    async def get_task_by_id(self, conn: asyncpg.Connection, task_id: str):
        query = "SELECT * FROM tasks WHERE task_id = $1"
        return await conn.fetchrow(query, task_id)
