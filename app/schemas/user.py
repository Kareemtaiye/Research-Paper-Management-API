from typing import Any
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class BaseUser(BaseModel):
    email: EmailStr
    role: str = "USER"


class UserCreate(BaseUser):
    full_name: str | None = None
    password: str


class UserOutput(BaseUser):
    model_config = ConfigDict(extra="ignore")

    id: str | UUID
    full_name: str | None = None
    created_at: Any


class UpdateUserRequest(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None
