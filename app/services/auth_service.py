from fastapi import Depends
from app.database import get_conn
from app.schemas.user import UserCreate
from app.repositories.auth_repo import AuthRepository


class AuthService:

    def __init__(self):
        self.repo = AuthRepository()

    async def register(self, conn, user_data: UserCreate):
        user = await self.repo.create_user(conn, user_data.model_dump())
        return user
