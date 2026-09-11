from app.core.email import EmailManager
from app.schemas.user import UserOutput
from app.tasks.celery_app import celery_app
from app.tasks.db_helpers import (
    get_paper_by_id,
    get_user_by_id,
    get_user_preference_sync,
)

email_manager = EmailManager()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_paper_notification(self, user_id: str, paper_id: str):
    """Send email notification when paper processing completes."""
    prefs = get_user_preference_sync(user_id)

    if not prefs or prefs["email_on_import_complete"]:
        user = get_user_by_id(user_id)
        paper = get_paper_by_id(paper_id)

        if not user or not paper:
            return {"error": "User or paper not found"}

        email_manager.send_paper_complete_email(
            f"Paper Ready: {paper['title']}",
            user["email"],
            user["full_name"],
            paper,
        )
        return {"status": "sent", "to": user["email"]}
    return


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_welcome_email(self, user: UserOutput):
    """Send welcome email to new user."""
    if not user:
        return {"error": "User not found"}

    email_manager.send_welcome_email(user.email, user.full_name)
    return {"status": "sent", "to": user.email}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_password_reset_email(self, user_email: str, token: str):
    """Send password reset email."""
    if not user_email or not token:
        return {"error": "User email or token not provided"}

    email_manager.send_password_reset_email(user_email, token)
    return {"status": "sent", "to": user_email}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_email_verification_email(
    self, user_email: str, token: str, full_name: str | None = None
):
    """Send verification email."""
    if not user_email or not token:
        return {"error": "User email or token not provided"}

    email_manager.send_email_verification_email(user_email, token, full_name)
    return {"status": "sent", "to": user_email}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_password_reset_success_email(self, user_email: str):
    """Send password reset success email."""
    if not user_email:
        return {"error": "User email not provided"}

    email_manager.send_password_reset_success_email(user_email)
    return {"status": "sent", "to": user_email}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_email_verification_success_email(
    self, user_email: str, full_name: str | None = None
):
    """Send success email on verification."""
    if not user_email:
        return {"error": "User email not provided"}

    email_manager.send_email_verification_success_email(user_email, full_name)
    return {"status": "sent", "to": user_email}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_feedback_email(self, user_email: str, type: str, message: str):
    if not user_email:
        return {"error": "User email not provided"}

    email_manager.send_feedback_email(user_email, type, message)
    return {"status": "sent", "to": "me"}
