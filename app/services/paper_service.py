from app.repositories.paper_repo import PaperRepository
from app.schemas.paper import PaperCreate


class PaperService:
    def __init__(self):
        self.repo = PaperRepository()

    async def create_paper_entry(self, conn, data: PaperCreate):
        return await self.repo.create_paper_entry(conn=conn, data=data.model_dump())

    async def get_all_papers(self, conn, id: str):
        return await self.repo.get_all_papers(conn=conn, paper_id=id)

    async def get_user_papers(self, conn, user_id: str):
        return await self.repo.get_user_papers(conn=conn, user_id=user_id)

    async def get_paper(self, conn, id: str):
        return await self.repo.get_paper(self, conn=conn, paper_id=id)

    async def delete_paper(self, conn, id: str):
        return await self.repo.delete_paper(conn=conn, paper_id=id)
