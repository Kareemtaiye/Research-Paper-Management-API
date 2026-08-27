from typing import Optional
from uuid import UUID
import uuid

from pydantic import BaseModel


class TaskStatusResponse(BaseModel):
    task_id: str
    paper_status: str
    paper_id: str | UUID
    title: Optional[str] = None


class TaskResponse(BaseModel):
    id: str | UUID
    task_id: str
    owner_id: str | UUID
    task_type: str
    status: str
    progress: str
    stage: Optional[str] = None
    stage_message: Optional[str] = None
    result: Optional[dict] = None
    error: Optional[str] = None
    paper_id: str | UUID
    completed_at: Optional[str] = None
    worker_name: Optional[str] = None
    created_at: str
    updated_at: str
