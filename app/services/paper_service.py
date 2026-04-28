from uuid import UUID

from app.core.exceptions import PaperNotFoundException
from app.repositories.paper_repo import PaperRepository

from app.schemas.request import ListQueryParams
from app.services.paper_tag_service import PaperTagsService
from app.utils.generators import gen_list_doc
from app.core.logger import logger


class PaperService:
    def __init__(self):
        self.repo = PaperRepository()

    async def create_paper_entry(self, conn, data: dict):
        paper = await self.repo.create_paper_entry(conn=conn, data=data)
        logger.info("Paper created successfully")
        return paper

    @gen_list_doc
    async def get_all_papers(self, conn, query_params: ListQueryParams):
        return await self.repo.get_all_papers(conn=conn, **query_params.model_dump())

    async def get_user_papers(self, conn, user_id: str | UUID, query_params):
        return await self.repo.get_user_papers(
            conn=conn, user_id=user_id, **query_params.model_dump()
        )

    async def get_paper(self, conn, id: str | UUID):
        paper = await self.repo.get_paper(conn=conn, paper_id=id)

        if not paper:
            raise PaperNotFoundException(id)
        return paper

    async def delete_paper(self, conn, id: str | UUID):
        count = await self.repo.delete_paper(conn=conn, paper_id=id)
        if count == 0:
            raise PaperNotFoundException(id)
        return count

    async def add_tag(self, conn, paper_id: str, tag_id: str):
        paper_tag_service = PaperTagsService()

        return await paper_tag_service.add_tag_to_paper(
            conn=conn, paper_id=paper_id, tag_id=tag_id
        )
