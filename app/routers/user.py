import email
from typing import Annotated

from pydantic import EmailStr

from app.core.security import hash_password, verify_password
from fastapi import APIRouter, Body, Depends, HTTPException, status
from app.core.database import get_conn
from app.dependencies.user import get_current_user
from app.exceptions.schemas import ErrorResponse
from app.schemas.user import UpdateUserRequest
from app.services.auth_service import AuthService
from app.services.user_service import UserService
from app.schemas.user import UpdateUserPreferencesRequest, UserPreferencesOutput

router = APIRouter(prefix="/user", tags=["users"])

auth_service = AuthService()
service = UserService()


@router.get("/me")
async def get_me(me=Depends(get_current_user)):
    return me


@router.patch("/me")
async def update_me(
    body: UpdateUserRequest,
    current_user=Depends(get_current_user),
    conn=Depends(get_conn),
):

    if current_user.email == "demo@kareemtaiye.com":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorResponse(
                status="error",
                code=status.HTTP_403_FORBIDDEN,
                message="Demo account is read-only",
            ),
        )
    await service.update_user_profile(
        conn=conn, user_id=current_user.id, email=body.email, full_name=body.full_name
    )

    return {"status": "success", "message": "User email updated successfully"}


@router.patch("/me/password")
async def change_password(
    current_password: Annotated[str, Body()],
    new_password: Annotated[str, Body()],
    current_user=Depends(get_current_user),
    conn=Depends(get_conn),
):
    if current_user.email == "demo@kareemtaiye.com":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorResponse(
                status="error",
                code=status.HTTP_403_FORBIDDEN,
                message="Demo account is read-only",
            ),
        )

    user = await auth_service.find_user_by_email(conn=conn, email=current_user.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=ErrorResponse(
                status="error",
                code=status.HTTP_404_NOT_FOUND,
                message="User not found",
            ),
        )

    if not verify_password(current_password, user["password"]):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=ErrorResponse(
                status="error",
                code=status.HTTP_400_BAD_REQUEST,
                message="Current password is incorrect",
            ),
        )

    await service.update_user_password(
        conn=conn,
        user_id=current_user.id,
        new_password_hash=hash_password(new_password),
    )

    return {"status": "success", "message": "Password updated successfully"}


@router.delete("/me")
async def delete_account(
    current_user=Depends(get_current_user), conn=Depends(get_conn)
):
    # Option 1 — check in delete/import endpoints
    if current_user.email == "demo@kareemtaiye.com":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorResponse(
                status="error",
                code=status.HTTP_403_FORBIDDEN,
                message="Demo account is read-only",
            ),
        )

    await service.delete_user(conn=conn, user_id=current_user.id)

    return {"status": "success", "message": "User account deleted successfully"}


@router.delete("/me/library")
async def clear_library(current_user=Depends(get_current_user), conn=Depends(get_conn)):
    if current_user.email == "demo@kareemtaiye.com":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=ErrorResponse(
                status="error",
                code=status.HTTP_403_FORBIDDEN,
                message="Demo account is read-only",
            ),
        )
    await service.clear_user_library(conn=conn, user_id=current_user.id)

    return {"status": "success", "message": "User library cleared successfully"}


@router.get("/me/preferences")
async def get_preferences(
    current_user=Depends(get_current_user), conn=Depends(get_conn)
):
    preferences = await service.get_user_preferences(conn=conn, user_id=current_user.id)
    return {"status": "success", "data": UserPreferencesOutput(**preferences)}


@router.patch("/me/preferences")
async def update_preferences(
    body: UpdateUserPreferencesRequest,
    current_user=Depends(get_current_user),
    conn=Depends(get_conn),
):

    prefs = await service.update_user_preferences(
        conn=conn,
        user_id=current_user.id,
        email_on_import_complete=body.email_on_import_complete,
        websocket_auto_reconnect=body.websocket_auto_reconnect,
    )

    return {"status": "success", "message": "Preferences updated", "data": prefs}
