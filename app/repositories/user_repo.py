import asyncpg

from app.core.database import with_connection


class UserRepository:
    @with_connection
    async def get_user_by_id(self, conn: asyncpg.Connection, id: str):
        query = "SELECT id, email, role, created_at FROM users WHERE id = $1"

        return await conn.fetchrow(query, id)
