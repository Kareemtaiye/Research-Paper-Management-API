from app.database import with_connection


class AuthRepository:
    async def create_user(self, conn, user_data: dict):
        query = """
        INSERT INTO users (email, role, password) 
        values ($1, $2, $3) 
        RETURNING id, email, role, created_at
        """

        return await conn.fetchrow(query, *user_data.values())
