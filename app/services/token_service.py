from app.repositories.token_repo import TokenRepository
from datetime import datetime


class TokenService:
    def __init__(self):
        self.token_repo = TokenRepository()

    async def create_password_reset_token(
        self, conn, user_id: str, token: str, expires_at: datetime
    ):
        return await self.token_repo.create_password_reset_token(
            conn=conn, user_id=user_id, token=token, expires_at=expires_at
        )

    async def get_password_reset_token(self, conn, token: str):
        return await self.token_repo.get_password_reset_token(conn=conn, token=token)

    async def delete_password_reset_token(self, conn, token: str):
        return await self.token_repo.delete_password_reset_token(conn=conn, token=token)

    async def create_email_verification_token(
        self, conn, user_id: str, token: str, expires_at: datetime
    ):
        return await self.token_repo.create_email_verification_token(
            conn=conn, user_id=user_id, token=token, expires_at=expires_at
        )

    async def get_email_verification_token(self, conn, token: str):
        return await self.token_repo.get_email_verification_token(
            conn=conn, token=token
        )

    async def delete_email_verification_token(self, conn, token: str):
        return await self.token_repo.delete_email_verification_token(
            conn=conn, token=token
        )
