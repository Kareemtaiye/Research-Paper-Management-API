import asyncpg

from app.core.database import with_connection


class AuthRepository:
    @with_connection
    async def create_user(
        self,
        user_data: dict,
        conn: asyncpg.Connection = None,
    ):
        query = """
        INSERT INTO users (email, role, password) 
        values ($1, $2, $3) 
        RETURNING id, email, role, created_at
        """

        return await conn.fetchrow(query, *user_data.values())

    @with_connection
    async def find_user_by_email(self, email: str, conn: asyncpg.Connection = None):
        query = """
        SELECT * FROM users WHERE email = $1
        """

        return await conn.fetchrow(query, email)
