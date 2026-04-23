from typing import Annotated
from fastapi import APIRouter, Depends, HTTPException, Header, Response
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from app.core.database import get_conn
from app.exceptions.schemas import ErrorResponse
from app.schemas.auth import LoginInput
from app.schemas.user import UserCreate
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth")


@router.post("/register", tags=["register"])
async def register_user(user_data: UserCreate, conn=Depends(get_conn)):
    service = AuthService()
    return await service.register(user_data=user_data, conn=conn)


@router.post("/token", tags=["token"])
async def login(
    response: Response,
    conn=Depends(get_conn),
    form_data: OAuth2PasswordRequestForm = Depends(),
    x_client_type: Annotated[
        str | None, Header
    ] = None,  # looking for custom header for mobile
):
    service = AuthService()

    # email and password
    token_data = await service.login(
        conn=conn,
        user_data=LoginInput(username=form_data.username, password=form_data.password),
    )

    if not token_data:
        raise HTTPException(
            status_code=400,
            detail=(ErrorResponse(code=400, message="Invalid email or password")),
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
            samesite="lax",
            max_age=604800,
            path="/auth/",
        )

    return JSONResponse(status_code=200, content={"status": "success", **data})
