from json import JSONDecodeError
import os

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.core.database import get_conn
from app.dependencies.user import get_current_user
from app.schemas.paper import ArxivImportResponse, ArxivImportRequest
from app.schemas.user import UserOutput
from app.services.paper_service import PaperService
from app.tasks.db_helpers import create_task_record
from app.tasks.paper_tasks import fetch_arxiv_paper_metadata
from app.utils.extract_arxiv_id import extract_arxiv_id

router = APIRouter(
    prefix="/papers-import",
    tags=["papers-import"],
)

service = PaperService()


@router.post("/import/arxiv", response_model=ArxivImportResponse)
async def upload_arxiv_paper(
    data: ArxivImportRequest,
    current_user: UserOutput = Depends(get_current_user),
    conn=Depends(get_conn),
):

    arxiv_id = extract_arxiv_id(data.arxiv_url)
    # Validate before construction
    if not arxiv_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Arxiv URL or ID. Expected format: https://arxiv.org/abs/2301.00001 or 2301.00001",
        )

    # Construct arxiv URL if user provided raw ID
    arxiv_url = (
        data.arxiv_url
        if data.arxiv_url.startswith("http")
        else f"https://arxiv.org/abs/{data.arxiv_url}"
    )

    # Temp entry data for arxiv paper(with no task id yet). also, def task id is None
    entry_data = {
        "temp_title": f"Arxiv Paper ({arxiv_id})",
        "owner_id": current_user.id,
        "arxiv_url": arxiv_url,
        "arxiv_id": arxiv_id,
        "task_id": None,
    }

    # Paper insert with status pending
    paper_entry = await service.create_arxiv_paper_entry(conn=conn, data=entry_data)

    # Start backgorund task to fetch metadata from Arxiv
    try:
        task = fetch_arxiv_paper_metadata.delay(
            paper_entry["id"], arxiv_id, current_user.id
        )
    except Exception as e:
        # Rollback paper entry if task fails to start
        await service.delete_paper(conn=conn, id=paper_entry["id"])
        print("Failed to start background task for Arxiv import:", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start background task for Arxiv import: arxiv_id={arxiv_id}.",
        )

    # Update paper entry with task id for tracking
    await service.update_paper_task_id(
        conn=conn, paper_id=paper_entry["id"], task_id=task.id
    )

    try:
        # Create task record in PostgreSQL
        create_task_record(
            task_id=task.id,
            owner_id=str(current_user.id),
            task_type="fetch_paper_metadata",
            paper_id=str(paper_entry["id"]),
        )
    except Exception as e:
        # Rollback paper entry and task if task record creation fails
        await service.delete_paper(conn=conn, id=paper_entry["id"])
        print("Failed to create task record in PostgreSQL:", str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create task record in PostgreSQL for Arxiv import: arxiv_id={arxiv_id}.",
        )

    # Return immediately
    return JSONResponse(
        status_code=status.HTTP_202_ACCEPTED,
        content={
            "status": "success",
            "data": jsonable_encoder(
                ArxivImportResponse(
                    paper_id=paper_entry["id"],
                    status=paper_entry["status"],
                    task_id=task.id,
                    message=f"Paper import queued. Poll /tasks/{task.id} for updates.",
                )
            ),
        },
    )
