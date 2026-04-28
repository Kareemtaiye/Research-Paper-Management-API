from app.repositories.tag_repo import TagRepository
from app.schemas.request import ListQueryParams


class TagService:
    def __init__(self):
        self.repo = TagRepository()

    async def get_all_tags(self, conn, query_params: ListQueryParams):
        return await self.repo.get_all_tags(
            conn=conn, page=query_params.page, per_page=query_params.per_page
        )
