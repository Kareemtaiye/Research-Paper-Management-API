from typing import Any

from pydantic import BaseModel


class ListResponse(BaseModel):  # A consistent format for all list endpoint
    data: list[Any]
    page: int = 1
    per_page: int = 20
    total: int
