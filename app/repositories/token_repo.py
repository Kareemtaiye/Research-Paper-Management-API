from datetime import datetime

from app.core.database import with_connection
import asyncpg


class TokenRepository:
    @with_connection
    async def create_password_reset_token(
        self, conn: asyncpg.Connection, user_id: str, token: str, expires_at: datetime
    ):
        query = """
            INSERT INTO password_reset_tokens (user_id, token, expires_at)
            VALUES ($1, $2, $3)
             ON CONFLICT (user_id) DO UPDATE
            SET token = $2, expires_at = $3, created_at = NOW()
            RETURNING *
        """
        return await conn.fetchrow(query, user_id, token, expires_at)

    @with_connection
    async def get_password_reset_token(self, conn: asyncpg.Connection, token: str):
        query = """
            SELECT * FROM password_reset_tokens
            WHERE token = $1 AND expires_at > NOW()
        """
        return await conn.fetchrow(query, token)

    @with_connection
    async def delete_password_reset_token(self, conn: asyncpg.Connection, token: str):
        query = "DELETE FROM password_reset_tokens WHERE token = $1"
        await conn.execute(query, token)

    @with_connection
    async def create_email_verification_token(
        self, conn: asyncpg.Connection, user_id: str, token: str, expires_at: datetime
    ):
        query = """
            INSERT INTO email_verification_tokens (user_id, token, expires_at)
            VALUES ($1, $2, $3)
            ON CONFLICT (user_id) DO UPDATE
            SET token = $2, expires_at = $3, created_at = NOW()
            RETURNING *
        """
        return await conn.fetchrow(query, user_id, token, expires_at)

    @with_connection
    async def get_email_verification_token(self, conn: asyncpg.Connection, token: str):
        query = """
            SELECT * FROM email_verification_tokens
            WHERE token = $1 AND expires_at > NOW()
        """
        return await conn.fetchrow(query, token)

    @with_connection
    async def delete_email_verification_token(
        self, conn: asyncpg.Connection, token: str
    ):
        query = "DELETE FROM email_verification_tokens WHERE token = $1"
        await conn.execute(query, token)
