from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict


# Manual creation
class PaperCreate(BaseModel):
    model_config = ConfigDict(extra="ignore")

    title: str  # required — user must provide at least a title
    content: str | None = None  # their notes


# Arxiv import
class ArxivImportRequest(BaseModel):
    arxiv_url: str  # accepts full URL or raw ID


class PaperResponse(BaseModel):
    id: str | UUID
    owner_id: str | UUID
    title: Optional[str] = None  # optional — arxiv import starts with no title
    content: Optional[str] = None
    arxiv_url: Optional[str] = None
    arxiv_id: Optional[str] = None
    authors: Optional[list[str]] = None
    abstract: Optional[str] = None
    published_at: Optional[str] = None
    categories: Optional[list[str]] = None
    status: Optional[str] = None
    task_id: Optional[str] = None
    created_at: Any
    updated_at: Any


class PaperUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None


class ArxivImportResponse(BaseModel):
    paper_id: str | UUID
    status: str
    task_id: str
    message: str
