from typing import Annotated

from fastapi import APIRouter, Body, Depends, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.core.database import get_conn
from app.dependencies.user import get_current_user
from app.schemas.paper import PaperCreate, PaperOuputData
from app.schemas.request import ListQueryParams
from app.schemas.response import ListResponse
from app.services.paper_service import PaperService


router = APIRouter(prefix="/papers", tags=["papers"])


@router.post("/")
async def create_paper_entry(
    data: PaperCreate,
    current_user=Depends(get_current_user),
    conn=Depends(get_conn),
):
    service = PaperService()
    data_obj = PaperCreate(title=data.title, content=data.content)

    paper_entry = await service.create_paper_entry(
        conn=conn, data={**data_obj.model_dump(), "owner_id": current_user["id"]}
    )

    return JSONResponse(
        status_code=201,
        content={
            "status": "success",
            "data": jsonable_encoder(PaperOuputData(**paper_entry)),
        },
    )


@router.get("/", response_model=ListResponse)
async def read_all_papers(
    params: Annotated[ListQueryParams, Query()], conn=Depends(get_conn)
):

    service = PaperService()
    data = await service.get_all_papers(conn=conn, query_params=params)

    response_obj = ListResponse(
        data=[dict(record) for record in data["data"]],
        page=params.page,
        per_page=params.per_page,
        total=data["count"],
    )

    return JSONResponse(status_code=200, content=jsonable_encoder(response_obj))
