from typing import Annotated
from fastapi import APIRouter, Cookie, Depends, HTTPException, Header, Response, Request
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordRequestForm
from app.core.database import get_conn
from app.dependencies.user import get_current_user
from app.exceptions.schemas import ErrorResponse
from app.schemas.auth import LoginInput
from app.schemas.user import UserCreate, UserOutput
from app.services.auth_service import AuthService
from app.core.logger import logger

router = APIRouter(prefix="/auth")

service = AuthService()

# cookie_option = {
#     "httponly": True,
#     "secure": False,
#     "samesite": "lax",
#     "max_age": 604800,
#     "path": "/auth/",
# }


@router.post("/register", tags=["register"])
async def register_user(user_data: UserCreate, conn=Depends(get_conn)):
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

    # email and password
    token_data = await service.login(
        conn=conn,
        user_data=LoginInput(username=form_data.username, password=form_data.password),
    )

    if not token_data:
        logger.warning("Invalid login attempt")
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
            secure=False,
            samesite="lax",
            max_age=604800,
            path="/auth/",
        )

    # FastAPI will use the 'response' parameter to send the cookies.
    return {"status": "success", **data}


@router.post("/logout", tags=["logout"])
async def logout(
    response: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
    conn=Depends(get_conn),
    current_user: UserOutput = Depends(get_current_user),
):

    if not refresh_token:
        return Response(status_code=204)  # Already logged out

    session = await service.logout(conn=conn, token=refresh_token)

    if not session:
        return Response(status_code=204)  # Session might be deleted(by logging out)

    # clearing the cookie
    response.delete_cookie(key="refresh_token")
    return Response(status_code=204)


@router.post("/refresh", tags=["refresh"])
async def refresh_token(
    reponse: Response,
    refresh_token: Annotated[str | None, Cookie()] = None,
    conn=Depends(get_conn),
):

    if not refresh_token:
        return JSONResponse(
            status_code=401,
            content=jsonable_encoder(
                ErrorResponse(
                    status="error", code=401, message="No refresh token provided"
                )
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
