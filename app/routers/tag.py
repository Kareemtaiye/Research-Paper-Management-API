from typing import Annotated

from fastapi import APIRouter, Depends, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.core.database import get_conn
from app.schemas.request import ListQueryParams
from app.schemas.response import ListResponse
from app.services.tag_service import TagService


router = APIRouter(prefix="/tags")

service = TagService()


@router.get("/", tags=["tags"])
async def read_all_tags(
    params: Annotated[ListQueryParams, Query()], conn=Depends(get_conn)
):
    data = await service.get_all_tags(conn=conn, query_params=params)

    response_data = ListResponse(
        data=[dict(record) for record in data["data"]],
        page=params.page,
        per_page=params.per_page,
        total=data["count"],
    )

    return JSONResponse(
        status_code=200,
        content={"status": "success", "data": jsonable_encoder(response_data)},
    )
