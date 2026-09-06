import asyncpg

from app.core.database import with_connection


class UserPreferenceRepository:
    @with_connection
    async def update_user_preferences(
        self,
        conn: asyncpg.Connection,
        email_on_import_complete: bool,
        websocket_auto_reconnect: bool,
        user_id: str,
    ):
        query = """
            INSERT INTO user_preferences (
            user_id,
            email_on_import_complete,
            websocket_auto_reconnect
        )
        VALUES ($1, $2, $3)
        ON CONFLICT (user_id) DO UPDATE SET
            email_on_import_complete = EXCLUDED.email_on_import_complete,
            websocket_auto_reconnect = EXCLUDED.websocket_auto_reconnect,
            updated_at = NOW()
        """
        status_str = await conn.execute(
            query, user_id, email_on_import_complete, websocket_auto_reconnect
        )
        operation, _, affected_row = status_str.rpartition(" ")
        return int(affected_row)

    @with_connection
    async def get_user_preferences(
        self,
        conn: asyncpg.Connection,
        user_id: str,
    ):
        query = """
            SELECT * FROM user_preferences
            WHERE user_id = $1
        """

        row = await conn.fetchrow(query, user_id)
        if not row:

            return {
                "email_on_import_complete": True,
                "websocket_auto_reconnect": True,
            }

        return dict(row)
