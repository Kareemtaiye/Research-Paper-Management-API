import asyncpg

from app.core.database import with_connection


class UserPreferenceRepository:

    @with_connection
    async def update_user_preferences(
        self,
        conn: asyncpg.Connection,
        email_on_import_complete: bool | None,
        websocket_auto_reconnect: bool | None,
        user_id: str,
    ):
        query = """
            INSERT INTO user_preferences (
                user_id,
                email_on_import_complete,
                websocket_auto_reconnect
            )
            VALUES (
                $1,
                COALESCE($2, TRUE),
                COALESCE($3, TRUE)
            )
            ON CONFLICT (user_id) DO UPDATE SET
                email_on_import_complete = COALESCE(
                    $2,
                    user_preferences.email_on_import_complete
                ),
                websocket_auto_reconnect = COALESCE(
                    $3,
                    user_preferences.websocket_auto_reconnect
                ),
                updated_at = NOW()
            RETURNING
                email_on_import_complete,
                websocket_auto_reconnect,
                updated_at
        """

        row = await conn.fetchrow(
            query,
            user_id,
            email_on_import_complete,
            websocket_auto_reconnect,
        )

        return dict(row)

    @with_connection
    async def get_user_preferences(
        self,
        conn: asyncpg.Connection,
        user_id: str,
    ):
        query = """
            SELECT
                email_on_import_complete,
                websocket_auto_reconnect,
                updated_at
            FROM user_preferences
            WHERE user_id = $1
        """

        row = await conn.fetchrow(query, user_id)

        if not row:
            return {
                "email_on_import_complete": True,
                "websocket_auto_reconnect": True,
            }

        return dict(row)
