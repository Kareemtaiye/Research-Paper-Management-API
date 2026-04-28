from app.repositories.session_repo import SessionRepository
from app.schemas.auth import SessionCreate
from app.core.exceptions import SessionNotFoundException


class SessionService:
    def __init__(self):
        self.repo = SessionRepository()

    async def create_session(self, conn, session_data: SessionCreate):
        return await self.repo.create_session(
            conn=conn, session_data=session_data.model_dump()
        )

    async def revoke_session(self, conn, id: str):
        count = await self.repo.revoke_session(conn=conn, id=id)

        if count == 0:
            raise SessionNotFoundException(id)
        return count

    async def get_session_by_id(self, conn, id: str):
        return await self.repo.get_session_by_id(conn=conn, id=id)

    async def delete_session_by_token(self, conn, token: str):
        count = await self.repo.delete_session_by_token(conn=conn, token=token)
        return count
