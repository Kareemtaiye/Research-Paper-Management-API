from app.core.logger import logger
from app.schemas.auth import LoginInput
from app.schemas.user import UserCreate
from app.repositories.auth_repo import AuthRepository
from app.core.security import (
    DUMMY_HASH,
    generate_access_token,
    generate_refresh_token,
    hash_password,
    verify_password,
)


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

        # Create a session
        # try:
        #     print()
        # except:
        access_token = generate_access_token(str(user["id"]))
        refresh_token = generate_refresh_token()

        logger.info(f"User {user["email"]} login successfully")
        return access_token, refresh_token
