from typing import Any, Optional
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr


class BaseUser(BaseModel):
    email: EmailStr


class UserCreate(BaseUser):
    full_name: str | None = None
    password: str


class UserOutput(BaseUser):
    model_config = ConfigDict(extra="ignore")

    role: str
    id: str | UUID
    full_name: str | None = None
    email_verified: bool
    created_at: Any


class UpdateUserRequest(BaseModel):
    email: EmailStr | None = None
    full_name: str | None = None


class UpdateUserPreferencesRequest(BaseModel):
    email_on_import_complete: Optional[bool] = None
    websocket_auto_reconnect: Optional[bool] = None


class UserPreferencesOutput(BaseModel):
    email_on_import_complete: bool
    websocket_auto_reconnect: bool
