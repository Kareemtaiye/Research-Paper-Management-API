# app/routers/feedback.py
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional

from app.tasks.email_tasks import send_feedback_email

router = APIRouter()


class FeedbackRequest(BaseModel):
    type: str  # "feedback" or "bug"
    message: str
    email: Optional[str] = None


@router.post("/feedback")
async def submit_feedback(
    body: FeedbackRequest,
    # no auth required — anyone can submit
):
    if not body.message.strip():
        return JSONResponse(
            status_code=400,
            content={"status": "error", "message": "Message cannot be empty"},
        )

    send_feedback_email.delay(body.email or "not-provided", body.type, body.message)

    return {"status": "success", "message": "Feedback received. Thank you"}
