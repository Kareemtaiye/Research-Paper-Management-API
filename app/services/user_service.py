from pydantic.v1 import EmailStr

from app.core.logger import logger
from app.core.security import hash_password
from app.repositories.paper_repo import PaperRepository
from app.repositories.task_repo import TaskRepository
from app.core.exceptions import UserNotFoundException
from app.repositories.user_repo import UserRepository
from app.repositories.auth_repo import AuthRepository


class UserService:
    def __init__(self):
        self.repo = UserRepository()
        self.paper_repo = PaperRepository()
        self.task_repo = TaskRepository()
        self.auth_repo = AuthRepository()

    async def get_user_by_id(self, conn, id: str):
        return await self.repo.get_user_by_id(conn=conn, id=id)

    async def get_user_by_email(self, conn, email: str):
        return await self.repo.get_user_by_email(conn=conn, email=email)

    async def update_user_email(self, conn, user_id: str, new_email: EmailStr):
        count = await self.repo.update_user_email(
            conn=conn, user_id=user_id, new_email=new_email
        )

        if count == 0:
            raise UserNotFoundException(user_id)
        logger.info(f"Updated user {user_id} with new email {new_email}")
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

    async def delete_user(self, conn, user_id: str):
        count = await self.repo.delete_user(conn=conn, user_id=user_id)

        if count == 0:
            raise UserNotFoundException(user_id)
        logger.info(f"Deleted user {user_id}")
        return count
