from hmac import new
from typing import Any

import asyncpg

from app.core.exceptions import SessionNotFoundException
from app.core.logger import logger
from app.schemas.auth import LoginInput, SessionCreate
from app.schemas.user import UserCreate
from app.repositories.auth_repo import AuthRepository
from app.core.security import (
    DUMMY_HASH,
    generate_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.services.session_service import SessionService

session_service = SessionService()


class AuthService:

    def __init__(self):
        self.repo = AuthRepository()

    async def register(self, conn, user_data: UserCreate):
        password_hash = hash_password(user_data.password)

        user = await self.repo.create_user(
            conn=conn, user_data={**user_data.model_dump(), "password": password_hash}
        )

        logger.info(f"User {user["email"]} signed up successfully")
        return user

    async def login(self, conn, user_data: LoginInput):
        user = await self.repo.find_user_by_email(conn=conn, email=user_data.username)

        if not user:
            verify_password(user_data.password, DUMMY_HASH)  # Solves timing attack
            return None

        password_match = verify_password(user_data.password, user["password"])
        if not password_match:
            return None

        access_token = generate_access_token(str(user["id"]))
        refresh_token = generate_refresh_token()

        # Create a session for the user
        session_service = SessionService()

        try:
            await session_service.repo.create_session(
                conn=conn,
                session_data={
                    "user_id": user["id"],
                    "token_hash": hash_token(refresh_token),
                },
            )
        except Exception as e:
            logger.exception(f"Failed to create session for user: {user["email"]}")
            raise

        logger.info(f"User {user["email"]} login successfully")
        return access_token, refresh_token

    async def logout(self, conn, token: str):

        return await session_service.repo.delete_session_by_token(
            conn=conn, token_hash=hash_token(token)
        )

    async def refresh_token(self, conn: asyncpg.Connection, refresh_token: str):
        # delete the old session and create a new session
        async with conn.transaction():
            user_id = await session_service.repo.delete_session_by_token(
                conn=conn, token_hash=hash_token(refresh_token)
            )

            if not user_id:
                raise SessionNotFoundException(refresh_token)

            # New refresh token
            new_refresh_token = generate_refresh_token()

            session: Any = await session_service.create_session(
                conn=conn,
                session_data=SessionCreate(
                    user_id=user_id, token_hash=hash_token(new_refresh_token)
                ),
            )

            logger.info(f"User with id: {user_id} refreshed their token")

            # New access token
            access_token = generate_access_token(data=str(session["user_id"]))
        return {"access_token": access_token, "refresh_token": new_refresh_token}
