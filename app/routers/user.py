from typing import Annotated

from pydantic import EmailStr

from app.core.security import hash_password, verify_password
from fastapi import APIRouter, Body, Depends
from fastapi.responses import JSONResponse
from app.core.database import get_conn
from app.dependencies.user import get_current_user
from app.schemas.user import UpdateUserRequest
from app.services.auth_service import AuthService
from app.services.user_service import UserService

router = APIRouter(prefix="/user", tags=["users"])

auth_service = AuthService()
service = UserService()


@router.get("/me")
async def get_me(me=Depends(get_current_user)):
    return me


# PATCH /users/me           → update email
# PATCH /users/me/password  → change password
# DELETE /users/me/library  → clear all papers and tasks
# DELETE /users/me          → delete account


@router.patch("/me")
async def update_me(
    body: UpdateUserRequest,
    current_user=Depends(get_current_user),
    conn=Depends(get_conn),
):
    await service.update_user_email(
        conn=conn, user_id=current_user.id, new_email=body.email
    )

    return {"status": "success", "message": "User email updated successfully"}


@router.patch("/me/password")
async def change_password(
    current_password: Annotated[str, Body()],
    new_password: Annotated[str, Body()],
    current_user=Depends(get_current_user),
    conn=Depends(get_conn),
):

    user = await auth_service.find_user_by_email(conn=conn, email=current_user.email)
    if not user:
        return JSONResponse(
            status_code=404,
            content={
                "status": "error",
                "message": "User not found",
            },
        )

    if not verify_password(current_password, user["password"]):
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": "Current password is incorrect",
            },
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
    await service.delete_user(conn=conn, user_id=current_user.id)

    return {"status": "success", "message": "User account deleted successfully"}


@router.delete("/me/library")
async def clear_library(current_user=Depends(get_current_user), conn=Depends(get_conn)):
    await service.clear_user_library(conn=conn, user_id=current_user.id)

    return {"status": "success", "message": "User library cleared successfully"}
