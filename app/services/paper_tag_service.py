from app.repositories.paper_tag_repo import PaperTagRepository


class PaperTagsService:
    def __init__(self):
        self.repo = PaperTagRepository()

    async def add_tag_to_paper(self, conn, paper_id: str, tag_id: str):
        return await self.repo.create_paper_tag(
            conn=conn, paper_id=paper_id, tag_id=tag_id
        )
