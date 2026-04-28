from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class BaseUser(BaseModel):
    email: EmailStr
    role: str = "USER"


class UserCreate(BaseUser):
    password: str


class UserOutput(BaseUser):
    model_config = ConfigDict(extra="ignore")

    id: str | UUID
    created_at: Any
