from typing import Optional
from uuid import UUID

from pydantic import BaseModel


class TaskResponse(BaseModel):
    task_id: str
    paper_status: str
    paper_id: str | UUID
    title: Optional[str] = None
