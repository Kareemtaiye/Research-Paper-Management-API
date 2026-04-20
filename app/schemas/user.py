from pydantic import BaseModel, EmailStr


class BaseUser(BaseModel):
    email: EmailStr
    role: str = "USER"


class UserCreate(BaseUser):
    password: str


class UserOutput(BaseUser):
    id: str
    created_at: str
