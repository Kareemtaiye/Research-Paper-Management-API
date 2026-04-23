from typing import Annotated

from fastapi import APIRouter, Body, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.core.database import get_conn
from app.dependencies.user import get_current_user
from app.schemas.paper import PaperCreate, PaperOuputData
from app.services.paper_service import PaperService


router = APIRouter(prefix="/papers", tags=["papers"])


@router.post("/")
async def create_paper_entry(
    data: PaperCreate,
    current_user=Depends(get_current_user),
    conn=Depends(get_conn),
):
    service = PaperService()
    data_obj = PaperCreate(
        title=data.title, owner_id=current_user["id"], content=data.content
    )
    paper_entry = await service.create_paper_entry(conn=conn, data=data_obj)

    # response_data = {**paper_entry, "owner_id": str(paper_entry["owner_id"])}
    # print((response_data["owner_id"]))

    return JSONResponse(
        status_code=201,
        content={
            "status": "success",
            "data": jsonable_encoder(PaperOuputData(**paper_entry)),
        },
    )
