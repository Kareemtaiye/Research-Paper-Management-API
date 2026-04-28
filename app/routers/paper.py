from typing import Annotated
from venv import logger

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from fastapi import Response, status

from app.core.database import get_conn
from app.dependencies.user import get_current_user
from app.exceptions.schemas import ErrorResponse
from app.schemas.paper import PaperCreate, PaperOuputData
from app.schemas.request import ListQueryParams
from app.schemas.response import ListResponse
from app.schemas.user import UserOutput
from app.services.paper_service import PaperService


router = APIRouter(prefix="/papers", tags=["papers"])
service = PaperService()


@router.post("/")
async def create_paper_entry(
    data: PaperCreate,
    current_user: UserOutput = Depends(get_current_user),
    conn=Depends(get_conn),
):

    data_obj = PaperCreate(title=data.title, content=data.content)

    paper_entry = await service.create_paper_entry(
        conn=conn, data={**data_obj.model_dump(), "owner_id": current_user.id}
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

    data = await service.get_all_papers(conn=conn, query_params=params)

    response_obj = ListResponse(
        data=[dict(record) for record in data["data"]],
        page=params.page,
        per_page=params.per_page,
        total=data["count"],
    )
    return JSONResponse(
        status_code=200,
        content={"status": "success", "data": jsonable_encoder(response_obj)},
    )


@router.get("/me", response_model=ListResponse)
async def read_my_papers(
    params: Annotated[ListQueryParams, Query()],
    conn=Depends(get_conn),
    current_user: UserOutput = Depends(get_current_user),
):

    data = await service.get_user_papers(
        conn=conn, user_id=current_user.id, query_params=params
    )

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


@router.get("/{paper_id}")
async def read_one_paper(
    paper_id: str,
    conn=Depends(get_conn),
    current_user: UserOutput = Depends(get_current_user),
):

    paper = await service.get_paper(conn=conn, id=str(paper_id))
    return JSONResponse(
        status_code=200, content={"status": "success", "data": jsonable_encoder(paper)}
    )


@router.delete("/{paper_id}")
async def delete_paper(
    paper_id: str,
    conn=Depends(get_conn),
    current_user: UserOutput = Depends(get_current_user),
):
    paper = await service.get_paper(conn=conn, id=paper_id)

    if paper["owner_id"] != current_user.id:
        logger.error(
            f"User {current_user.email} tried to delete non owned paper: {paper_id}"
        )
        raise HTTPException(
            status_code=403,
            detail=jsonable_encoder(
                ErrorResponse(
                    status="error",
                    code=403,
                    message="Cannot delete paper that is not your own",
                )
            ),
        )

    await service.delete_paper(conn=conn, id=paper_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
