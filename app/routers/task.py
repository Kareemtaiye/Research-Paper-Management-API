from urllib import response

from celery.result import AsyncResult
from fastapi import APIRouter, Depends
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

from app.core.database import get_conn
from app.dependencies.user import get_current_user
from app.schemas.task import TaskResponse
from app.schemas.user import UserOutput
from app.services.task_service import TaskService
from app.tasks.celery_app import celery_app

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)

service = TaskService()


@router.get("{task_id}", response_model=TaskResponse)
async def get_task_status(
    task_id: str,
    conn=Depends(get_conn),
    current_user: UserOutput = Depends(get_current_user),
):
    paper_row = await service.get_paper_task_status(conn=conn, task_id=task_id)

    task = AsyncResult(task_id, app=celery_app)

    print(dict(paper_row))

    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "data": {
                **jsonable_encoder(
                    TaskResponse(
                        task_id=str(task_id),
                        paper_status=paper_row["status"],
                        paper_id=str(paper_row["id"]),
                        title=paper_row["title"],
                    )
                ),
            },
        },
    )
