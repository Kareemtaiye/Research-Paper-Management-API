import asyncpg

from app.core.database import with_connection


class SessionRepository:
    @with_connection
    async def create_session(self, conn: asyncpg.Connection, session_data: dict):
        query = """
            INSERT INTO sessions (user_id, token_hash)
            VALUES ($1, $2) 
            RETURNING * 
        """

        return await conn.fetchrow(query, *session_data.values())

    @with_connection
    async def get_session_by_id(self, conn: asyncpg.Connection, id: str):
        query = "SELECT * FROM sessions WHERE id = $1"

        return await conn.fetchrow(query, id)

    @with_connection
    async def get_session_by_token(self, conn: asyncpg.Connection, token: str):
        query = "SELECT * FROM sessions WHERE token_hash = $1"

        return await conn.fetchrow(query, token)

    @with_connection
    async def revoke_session(self, conn: asyncpg.Connection, id: str):
        """Returns the number of updated sessions row - 0 if no row was updated"""
        query = "UPDATE sessions SET revoked_at = NOW()"

        status_str = await conn.execute(query, id)
        operation, _, affected_row = status_str.rpartition(" ")
        return int(affected_row)

    @with_connection
    async def delete_session_by_token(self, conn: asyncpg.Connection, token_hash: str):
        query = """
            DELETE FROM sessions 
            WHERE token_hash = $1 
            RETURNING user_id
        """

        return await conn.fetchval(query, token_hash)
