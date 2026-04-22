from pydantic import BaseModel


class ErrorResponse(BaseModel):
    status: str = "error"
    code: int
    message: str
    details: str | dict | list[dict] | None = None
