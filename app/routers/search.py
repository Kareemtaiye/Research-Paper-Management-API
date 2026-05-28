from fastapi import APIRouter, Depends, Query
from app.dependencies.user import get_current_user
from app.schemas.user import UserOutput
from app.services.search_service import search_papers

router = APIRouter(tags=["search"])


@router.get("/papers/search")
async def search(
    q: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=50),
    offset: int = Query(0, ge=0),
    category: str = Query(None),
    from_date: str = Query(None),
    current_user: UserOutput = Depends(get_current_user),
):
    results = await search_papers(
        query=q,
        owner_id=str(current_user.id),
        limit=limit,
        offset=offset,
        category=category,
        from_date=from_date,
    )
    return {"status": "success", "data": results}
