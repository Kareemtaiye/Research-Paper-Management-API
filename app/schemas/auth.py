from uuid import UUID

from pydantic import BaseModel, EmailStr
from app.schemas.user import BaseUser


class LoginInput(BaseModel):
    username: EmailStr
    password: str


class LoginOutput(BaseUser):
    id: str
    created_at: str


class SessionCreate(BaseModel):
    user_id: str | UUID
    token_hash: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResendVerificationRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    new_password: str
    # email_confirm: EmailStr


class VerifyEmailRequest(BaseModel):
    token: str
