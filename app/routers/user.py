from fastapi import APIRouter, Depends

from app.dependencies.user import get_current_user

router = APIRouter(prefix="/user", tags=["users"])


@router.get("/me")
async def get_me(me=Depends(get_current_user)):
    return me
