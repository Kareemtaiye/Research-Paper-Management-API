from importlib import resources
from typing import Callable

import asyncpg
from fastapi import Depends, HTTPException, status

from app.core.database import get_conn
from app.core.exceptions import ResourceNotFoundException
from app.core.logger import logger
from app.dependencies.user import get_current_user
from app.exceptions.schemas import ErrorResponse
from app.schemas.user import UserOutput


# --------V1------------ Beatiful version by the way. I just love the simplicity
def restricted_to(*allowed_roles: str):
    async def role_checker(current_user: UserOutput = Depends(get_current_user)):
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorResponse(
                    status="error",
                    code=status.HTTP_403_FORBIDDEN,
                    message="You do not have permission to access this resource",
                ),
            )

        return current_user

    return role_checker


# ----- V2 --------
class RequireRole:
    def __init__(self, allowed_roles: list[str]):
        self.allowed_roles = allowed_roles

    def __call__(self, user: UserOutput = Depends(get_current_user)):
        if user.role not in self.allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorResponse(
                    status="error",
                    code=status.HTTP_403_FORBIDDEN,
                    message="You do not have permission to access this resource",
                ),
            )

        # return user


# ----- V3 -------- Upgrade
class RequireOwnerOrRole:
    def __init__(
        self, fetch_resource_function: Callable, allowed_roles: list[str] = ["admin"]
    ):
        self.fetch_resource_function = fetch_resource_function
        self.allowed_roles = allowed_roles

    async def __call__(
        self,
        resource_id: str,  # FastAPI will pull this from the URL path
        current_user: UserOutput = Depends(get_current_user),
        conn: asyncpg.Connection = Depends(get_conn),
    ):
        # 1 fetch the resource
        resource = await self.fetch_resource_function(conn, resource_id)

        if not resource:
            raise ResourceNotFoundException(resource_id)

        # adnin override
        if current_user.role in self.allowed_roles:
            logger.info(
                f"Admin {current_user.email} accessing resource: {str(resource)}"
            )
            return resource

        # 3. Check Ownership
        # assuming the DB records have an 'owner_id' or 'user_id' field
        resource_owner = resource.get("owner_id") or resource.get("user_id")

        if str(resource_owner) != str(current_user.id):
            logger.exception(
                f"User {current_user.email} tried to access resource belonging to user: {resource_owner}"
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=ErrorResponse(
                    status="error",
                    code=status.HTTP_403_FORBIDDEN,
                    message="You do not have permission to access this resource",
                ),
            )

        return resource
