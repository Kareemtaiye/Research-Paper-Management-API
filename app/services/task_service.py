from app.core.exceptions import TaskNotFoundException
from app.repositories.paper_repo import PaperRepository


class TaskService:
    def __init__(self) -> None:
        self.paper_repo: PaperRepository = PaperRepository()

    async def get_paper_task_status(self, conn, task_id: str):
        paper = await self.paper_repo.get_paper_by_task_id(conn=conn, task_id=task_id)

        if not paper:
            raise TaskNotFoundException(task_id)

        return paper
