from pydantic import BaseModel, ConfigDict


class QueryParams(BaseModel):
    q: str | None = None


class ListQueryParams(BaseModel):

    model_config = ConfigDict({"extra": "ignore"})

    page: int = 1
    per_page: int = 20
