from typing import Annotated
from urllib import response

from celery.result import AsyncResult
from fastapi import APIRouter, Depends, Query
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from pytest import param

from app.core.database import get_conn
from app.dependencies.user import get_current_user
from app.schemas.request import ListQueryParams
from app.schemas.response import ListResponse
from app.schemas.task import TaskResponse, TaskStatusResponse
from app.schemas.user import UserOutput
from app.services.task_service import TaskService
from app.tasks.celery_app import celery_app

router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
)

service = TaskService()


@router.get("/", response_model=ListResponse)
async def get_all_tasks(
    params: Annotated[ListQueryParams, Query()],
    conn=Depends(get_conn),
    current_user: UserOutput = Depends(get_current_user),
):
    data = await service.get_all_tasks(
        conn=conn, user_id=str(current_user.id), query_params=params
    )

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


@router.get("/tasks/{task_id}")
async def get_task(
    task_id: str, current_user=Depends(get_current_user), conn=Depends(get_db)
):
    row = await conn.fetchrow(
        """
        SELECT t.*, p.title as paper_title
        FROM tasks t
        LEFT JOIN papers p ON t.paper_id = p.id
        WHERE t.task_id = $1 AND t.owner_id = $2
    """,
        task_id,
        str(current_user.id),
    )

    if not row:
        raise HTTPException(404, "Task not found")

    return {"status": "success", "data": dict(row)}


@router.get("/tasks/stats/summary")
async def get_tasks_summary(
    current_user=Depends(get_current_user), conn=Depends(get_db)
):
    """Quick stats — useful for dashboard."""
    rows = await conn.fetch(
        """
        SELECT status, COUNT(*) as count
        FROM tasks
        WHERE owner_id = $1
        GROUP BY status
    """,
        str(current_user.id),
    )

    summary = {r["status"]: r["count"] for r in rows}

    return {
        "status": "success",
        "data": {
            "total": sum(summary.values()),
            "pending": summary.get("pending", 0),
            "processing": summary.get("processing", 0),
            "completed": summary.get("completed", 0),
            "failed": summary.get("failed", 0),
        },
    }


@router.get("{task_id}", response_model=TaskStatusResponse)
async def get_task_status(
    task_id: str,
    conn=Depends(get_conn),
    current_user: UserOutput = Depends(get_current_user),
):
    paper_row = await service.get_paper_task_status(conn=conn, task_id=task_id)

    task = AsyncResult(task_id, app=celery_app)

    # if task.state == "PENDING" and not celery_app.backend.get(task.id):
    #     return JSONResponse(
    #         status_code=404,
    #         content={"status": "error", "message": "Task not found"},
    #     )

    print(dict(paper_row))

    return JSONResponse(
        status_code=200,
        content={
            "status": "success",
            "data": {
                **jsonable_encoder(
                    TaskStatusResponse(
                        task_id=str(task_id),
                        paper_status=paper_row["status"],
                        paper_id=str(paper_row["id"]),
                        title=paper_row["title"],
                    )
                ),
            },
        },
    )
