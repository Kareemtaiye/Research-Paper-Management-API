from app.repositories.user_repo import UserRepository


class UserService:
    def __init__(self):
        self.repo = UserRepository()

    async def get_user_by_id(self, conn, id: str):
        return await self.repo.get_user_by_id(conn=conn, id=id)
