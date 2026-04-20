import json

from fastapi import APIRouter, Depends
from app.database import get_conn
from app.schemas.user import UserCreate, UserOutput
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth")


@router.post("/register", tags=["register"])
async def regiser(user_data: UserCreate, conn=Depends(get_conn)):
    service = AuthService()
    return await service.register(conn, user_data)
