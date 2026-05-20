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

    async def create_arxiv_paper_entry(self, conn, data: dict):
        paper = await self.repo.create_arxiv_paper_entry(conn=conn, data=data)
        logger.info("Arxiv paper entry created with pending status")
        return paper

    async def update_paper_task_id(self, conn, paper_id: str, task_id: str):
        count = await self.repo.update_paper_task_id(
            conn=conn, paper_id=paper_id, task_id=task_id
        )

        if count == 0:
            raise PaperNotFoundException(paper_id)
        logger.info(f"Updated paper {paper_id} with task id {task_id}")
        return count

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

    async def update_paper_status(self, conn, id: str, status_str: str):
        count = await self.repo.update_paper_status(
            conn=conn, paper_id=id, status_str=status_str
        )

        if count == 0:
            raise PaperNotFoundException(id)
        return count

    async def update_paper_metadata(
        self,
        conn,
        paper_id: str,
        title: str,
        abstract: str,
        authors: list[str],
        categories: list[str],
        published_at: str,
        status: str,
    ):
        count = await self.repo.update_paper_metadata(
            conn=conn,
            paper_id=paper_id,
            title=title,
            abstract=abstract,
            authors=authors,
            categories=categories,
            published_at=published_at,
            status=status,
        )

        if count == 0:
            raise PaperNotFoundException(paper_id)
        return count
