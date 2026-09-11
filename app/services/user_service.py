import email

from pydantic.v1 import EmailStr

from app.core.logger import logger
from app.core.security import hash_password
from app.repositories.paper_repo import PaperRepository
from app.repositories.task_repo import TaskRepository
from app.core.exceptions import UserNotFoundException
from app.repositories.user_repo import UserRepository
from app.repositories.auth_repo import AuthRepository
from app.repositories.user_preference_repo import UserPreferenceRepository


class UserService:
    def __init__(self):
        self.repo = UserRepository()
        self.paper_repo = PaperRepository()
        self.task_repo = TaskRepository()
        self.auth_repo = AuthRepository()
        self.user_preference_repo = UserPreferenceRepository()

    async def get_user_by_id(self, conn, id: str):
        return await self.repo.get_user_by_id(conn=conn, id=id)

    async def get_user_by_email(self, conn, email: str):
        return await self.repo.get_user_by_email(conn=conn, email=email)

    async def update_user_profile(
        self, conn, user_id: str, email: EmailStr | None, full_name: str | None
    ):
        count = await self.repo.update_user_profile(
            conn=conn, user_id=user_id, email=email, full_name=full_name
        )

        if count == 0:
            raise UserNotFoundException(user_id)
        logger.info(
            f"Updated user {user_id} with email {email} and full name {full_name}"
        )
        return count

    async def update_user_password(
        self,
        conn,
        user_id: str,
        new_password_hash: str,
    ):

        count = await self.repo.update_user_password(
            conn=conn, user_id=user_id, new_password_hash=new_password_hash
        )

        if count == 0:
            raise UserNotFoundException(user_id)
        logger.info(f"Updated user {user_id} with new password hash")
        return count

    async def mark_email_verified(self, conn, user_id: str):
        count = await self.repo.mark_email_verified(conn=conn, user_id=user_id)

        if count == 0:
            raise UserNotFoundException(user_id)
        logger.info(f"Marked email verified for user {user_id}")
        return count

    async def delete_user(self, conn, user_id: str):
        count = await self.repo.delete_user(conn=conn, user_id=user_id)

        if count == 0:
            raise UserNotFoundException(user_id)
        logger.info(f"Deleted user {user_id}")
        return count

    async def clear_user_library(self, conn, user_id: str):
        # Delete all papers and tasks associated with the user
        async with conn.transaction():
            await self.paper_repo.delete_user_papers(conn=conn, user_id=user_id)
            await self.task_repo.delete_user_tasks(conn=conn, user_id=user_id)
        logger.info(f"Cleared library for user {user_id}")

    async def update_user_preferences(
        self,
        conn,
        user_id: str,
        email_on_import_complete: bool | None,
        websocket_auto_reconnect: bool | None,
    ):
        return await self.user_preference_repo.update_user_preferences(
            conn=conn,
            user_id=user_id,
            email_on_import_complete=email_on_import_complete,
            websocket_auto_reconnect=websocket_auto_reconnect,
        )

    async def get_user_preferences(self, conn, user_id: str):
        return await self.user_preference_repo.get_user_preferences(
            conn=conn, user_id=user_id
        )
