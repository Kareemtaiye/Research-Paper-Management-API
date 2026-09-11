from datetime import datetime, timedelta
from typing import Annotated
from fastapi import (
    APIRouter,
    Cookie,
    Depends,
    HTTPException,
    Header,
    Query,
    Response,
    status,
)
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from app.core.database import get_conn
from app.core.security import hash_password
from app.dependencies.user import get_current_user
from app.exceptions.schemas import ErrorResponse
from app.schemas.auth import (
    ForgotPasswordRequest,
    LoginInput,
    ResendVerificationRequest,
    ResetPasswordRequest,
    VerifyEmailRequest,
)
from app.schemas.user import UserCreate, UserOutput
from app.services.user_service import UserService
from app.services.auth_service import AuthService
from app.core.logger import logger
import secrets
from app.services.token_service import TokenService

from app.tasks import email_tasks

router = APIRouter(prefix="/auth")

service = AuthService()
token_service = TokenService()
user_service = UserService()
# cookie_option = {
#     "httponly": True,
#     "secure": False,
#     "samesite": "lax",
#     "max_age": 604800,
#     "path": "/auth/",
# }


@router.post("/register", tags=["register"])
async def register_user(user_data: UserCreate, conn=Depends(get_conn)):
    user, token = await service.register(user_data=user_data, conn=conn)
    email_tasks.send_email_verification_email.delay(user["email"], token)

    return JSONResponse(
        status_code=201, content=jsonable_encoder({"status": "success", "data": user})
    )


@router.post("/token", tags=["token"])
async def login(
    response: Response,
    conn=Depends(get_conn),
    form_data: OAuth2PasswordRequestForm = Depends(),
    x_client_type: Annotated[
        str | None, Header
    ] = None,  # looking for custom header for mobile
):

    # email and password
    token_data = await service.login(
        conn=conn,
        user_data=LoginInput(username=form_data.username, password=form_data.password),
    )

    if not token_data:
        logger.warning("Invalid login attempt")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                status="error",
                code=status.HTTP_400_BAD_REQUEST,
                message="Invalid email or password",
            ),
        )

    access_token, refresh_token = token_data
    data = {"access_token": access_token, "token_type": "bearer"}

    if x_client_type == "mobile":
        data.update({"refresh_token": refresh_token})
    else:
        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            secure=True,
            samesite="none",
            max_age=604800,
            path="/",
        )

    # FastAPI will use the 'response' parameter to send the cookies.
    return {"status": "success", **data}


@router.post("/logout", tags=["logout"])
async def logout(
    response: Response,  # 👈 FastAPI tracks this object
    refresh_token: Annotated[str | None, Cookie()] = None,
    conn=Depends(get_conn),
    current_user: UserOutput = Depends(get_current_user),
):
    if not refresh_token:
        response.status_code = 204
        return response

    session = await service.logout(conn=conn, token=refresh_token)

    if not session:
        response.status_code = 204
        return response

    response.delete_cookie(
        key="refresh_token",
        path="/",
        samesite="none",
        secure=True,
        httponly=True,
    )

    response.status_code = 204  # 👈 Set status code on the tracked object
    return response


@router.post("/refresh", tags=["refresh"])
async def refresh_token(
    reponse: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
    conn=Depends(get_conn),
):

    if not refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=ErrorResponse(
                status="error",
                code=status.HTTP_401_UNAUTHORIZED,
                message="No refresh token provided",
            ),
        )

    data = await service.refresh_token(conn=conn, refresh_token=refresh_token)

    # Handles refresh for web only.
    reponse.set_cookie(
        key="refresh_token",
        value=data["refresh_token"],
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=604800,
        path="/auth/",
    )

    return {
        "status": "success",
        "access_token": data["access_token"],
        "token_type": "bearer",
    }


# POST /auth/forgot-password    → accepts email, sends reset link
# POST /auth/reset-password     → accepts token + new password, resets it

# POST /auth/verify-email       → accepts verification token, marks email verified
# POST /auth/resend-verification → resends verification email


@router.post("/forgot-password", tags=["forgot-password"])
async def forgot_password(body: ForgotPasswordRequest, conn=Depends(get_conn)):
    user = await service.find_user_by_email(conn=conn, email=body.email)

    # Always return success — don't reveal if email exists
    if not user:
        logger.warning(f"Forgot password attempt for non-existent email: {body.email}")
        return {
            "status": "success",
            "message": "If the email exists, a reset link has been sent.",
        }

    # Generate reset token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.utcnow() + timedelta(hours=1)

    await token_service.create_password_reset_token(
        conn=conn, user_id=user["id"], token=token, expires_at=expires_at
    )

    # Send reset email
    email_tasks.send_password_reset_email.delay(user["email"], token)

    return {
        "status": "success",
        "message": "If that email exists, a reset link was sent",
    }


@router.post("/reset-password", tags=["reset-password"])
async def reset_password(
    body: ResetPasswordRequest, token: Annotated[str, Query()], conn=Depends(get_conn)
):
    token_row = await token_service.get_password_reset_token(conn=conn, token=token)

    if not token_row:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                status="error",
                code=status.HTTP_400_BAD_REQUEST,
                message="Invalid or expired reset token.",
            ),
        )

    if token_row["expires_at"] < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                status="error",
                code=status.HTTP_400_BAD_REQUEST,
                message="Invalid or expired reset token.",
            ),
        )

    hashed_password = hash_password(body.new_password)
    await user_service.update_user_password(
        conn=conn, user_id=token_row["user_id"], new_password_hash=hashed_password
    )

    user = await user_service.get_user_by_id(conn=conn, id=token_row["user_id"])

    email_tasks.send_password_reset_success_email.delay(user["email"])

    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": "Password reset successful",
        },
    )


@router.post("/verify-email", tags=["verify-email"])
async def verify_email(body: VerifyEmailRequest, conn=Depends(get_conn)):
    result = await service.verify_email(conn=conn, token=body.token)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                status="error",
                code=status.HTTP_400_BAD_REQUEST,
                message="Invalid or expired verification token.",
            ),
        )

    user, newly_verified = result

    if newly_verified:
        email_tasks.send_email_verification_success_email.delay(user["email"])

    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "message": "Email verified successfully",
        },
    )


@router.post("/resend-verification", tags=["resend-verification"])
async def resend_verification(body: ResendVerificationRequest, conn=Depends(get_conn)):
    result = await service.resend_verification(conn=conn, email=body.email)

    if result:
        user, token = result
        email_tasks.send_email_verification_email.delay(user["email"], token)
    else:
        logger.warning(f"Resend verification skipped for email: {body.email}")

    return {
        "status": "success",
        "message": "If that email exists and is unverified, a verification link was sent",
    }
