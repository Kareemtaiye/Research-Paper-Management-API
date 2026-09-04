import asyncpg

from app.core.database import with_connection


class UserRepository:
    @with_connection
    async def get_user_by_id(self, conn: asyncpg.Connection, id: str):
        query = "SELECT id, email, full_name, role, is_deleted, created_at FROM users WHERE id = $1"

        return await conn.fetchrow(query, id)

    @with_connection
    async def get_user_by_email(self, conn: asyncpg.Connection, email: str):
        query = "SELECT id, email, full_name, role, is_deleted, created_at FROM users WHERE email = $1"

        return await conn.fetchrow(query, email)

    @with_connection
    async def update_user_email(
        self, conn: asyncpg.Connection, user_id: str, new_email: str
    ):
        query = "UPDATE users SET email = $1 WHERE id = $2"
        status_str = await conn.execute(query, new_email, user_id)
        operation, _, affected_row = status_str.rpartition(" ")
        return int(affected_row)

    @with_connection
    async def update_user_password(
        self, conn: asyncpg.Connection, user_id: str, new_password_hash: str
    ):
        query = "UPDATE users SET password = $1 WHERE id = $2"
        status_str = await conn.execute(query, new_password_hash, user_id)
        operation, _, affected_row = status_str.rpartition(" ")
        return int(affected_row)

    @with_connection
    async def update_user_full_name(
        self, conn: asyncpg.Connection, user_id: str, new_full_name: str
    ):
        query = "UPDATE users SET full_name = $1 WHERE id = $2"
        status_str = await conn.execute(query, new_full_name, user_id)
        operation, _, affected_row = status_str.rpartition(" ")
        return int(affected_row)

    @with_connection
    async def delete_user(self, conn: asyncpg.Connection, user_id: str):
        query = "UPDATE users SET is_deleted = TRUE WHERE id = $1"
        status_str = await conn.execute(query, user_id)
        operation, _, affected_row = status_str.rpartition(" ")
        return int(affected_row)
