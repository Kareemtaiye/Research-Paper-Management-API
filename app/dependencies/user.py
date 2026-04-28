import token
from typing import Annotated

from fastapi import Depends, HTTPException
from app.core.database import get_conn
from app.core.security import oauth2_scheme, verify_jwt
from app.exceptions.schemas import ErrorResponse
from app.schemas.user import UserOutput
from app.services.user_service import UserService


async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)], conn=Depends(get_conn)
) -> UserOutput:

    if not token:
        raise HTTPException(
            status_code=401,
            detail=ErrorResponse(status="error", code=401, message="Not Authenticated"),
        )

    payload = verify_jwt(token)

    service = UserService()
    user = await service.get_user_by_id(conn=conn, id=payload.get("sub"))

    if not user:
        raise HTTPException(
            status_code=400,
            detail=ErrorResponse(code=400, message="Invalid access token"),
        )

    return UserOutput(**user)
