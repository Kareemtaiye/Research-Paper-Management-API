from app.core.exceptions import TaskNotFoundException
from app.repositories.paper_repo import PaperRepository
from app.repositories.task_repo import TaskRepository
from app.schemas.request import ListQueryParams


class TaskService:
    def __init__(self) -> None:
        self.paper_repo: PaperRepository = PaperRepository()
        self.task_repo: TaskRepository = TaskRepository()

    async def get_paper_task_status(self, conn, task_id: str):
        paper = await self.paper_repo.get_paper_by_task_id(conn=conn, task_id=task_id)

        if not paper:
            raise TaskNotFoundException(task_id)

        return paper

    async def get_all_tasks(self, conn, user_id: str, query_params: ListQueryParams):
        return await self.task_repo.get_all_tasks(
            conn=conn, user_id=user_id, **query_params.model_dump()
        )
