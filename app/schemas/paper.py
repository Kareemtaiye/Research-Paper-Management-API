from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class PaperCreate(BaseModel):

    model_config = ConfigDict(extra="ignore")

    title: str
    owner_id: str | UUID
    content: str | None = None


class PaperOuputData(PaperCreate):
    created_at: Any
    updated_at: Any
