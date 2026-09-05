import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from app.core.email import EmailManager
from app.schemas.user import UserOutput
from app.tasks.celery_app import celery_app
from app.tasks.db_helpers import get_paper_by_id, get_user_by_id
from app.core.config import settings

SMTP_HOST = settings.mail_hog_smtp_host
SMTP_PORT = settings.mail_hog_smtp_port
FROM_EMAIL = settings.mail_hog_from_email
email_manager = EmailManager()


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_paper_notification(self, user_id: str, paper_id: str):
    """Send email notification when paper processing completes."""
    user = get_user_by_id(user_id)
    paper = get_paper_by_id(paper_id)

    if not user or not paper:
        return {"error": "User or paper not found"}

    email_subject = f"Paper Ready: {paper['title']}"
    # Build email
    msg = MIMEMultipart("alternative")
    msg["Subject"] = email_subject
    msg["From"] = FROM_EMAIL
    msg["To"] = user["email"]

    # Plain text version
    text = f"""
    Hi {user['email']},

    Your paper has been successfully imported:

    Title:      {paper['title']}
    Authors:    {', '.join(paper['authors'] or [])}
    Published:  {paper['published_at']}
    Link:       {paper['arxiv_url']}

    View it in your dashboard.
            """

    # HTML version
    html = f"""
    <html><body>
    <h2>Paper Successfully Imported</h2>
    <p><strong>Title:</strong> {paper['title']}</p>
    <p><strong>Authors:</strong> {', '.join(paper['authors'] or [])}</p>
    <p><strong>Published:</strong> {paper['published_at']}</p>
    <p><a href="{paper['arxiv_url']}">View on Arxiv</a></p>
    </body></html>
            """

    msg.attach(MIMEText(text, "plain"))
    msg.attach(MIMEText(html, "html"))

    if settings.is_production:
        email_manager.send_paper_complete_email(
            email_subject, user["email"], user["full_name"], paper
        )
    else:
        # mailhog, locally
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.sendmail(FROM_EMAIL, user["email"], msg.as_string())

    return {"status": "sent", "to": user["email"]}


# @celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
# def send_paper_import_failed_notification(self)


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_welcome_email(self, user: UserOutput):
    """Send welcome email to new user."""
    if not user:
        return {"error": "User not found"}

    if settings.is_production:
        email_manager.send_welcome_email(user.email, user.full_name)
    else:
        # mailhog, locally
        subject = "Welcome to PaperBase"
        hi = f"Hi {user.full_name or user.email.split('@')[0]},"
        html = f"""
        <html><body>
        <h2>Welcome to PaperBase</h2>
        <p>{hi}</p>
        <p>Thank you for signing up! We're excited to have you on board.</p>
        </body></html>
                """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = FROM_EMAIL
        msg["To"] = user.email
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.sendmail(FROM_EMAIL, user.email, msg.as_string())

    return {"status": "sent", "to": user.email}


@celery_app.task(bind=True, max_retries=3, default_retry_delay=30)
def send_password_reset_email(self, user_email: str, token: str):
    """Send password reset email."""
    if not user_email or not token:
        return {"error": "User email or token not provided"}

    if settings.is_production:
        email_manager.send_password_reset_email(user_email, token)
    else:
        # mailhog, locally
        subject = "Password Reset Request"
        reset_link = f"{settings.frontend_url_local}/reset-password?token={token}"
        html = f"""
        <html><body>
        <h2>Password Reset Request</h2>
        <p>Click the link below to reset your password:</p>
        <a href="{reset_link}">Reset Password</a>
        </body></html>
                """
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = FROM_EMAIL
        msg["To"] = user_email
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.sendmail(FROM_EMAIL, user_email, msg.as_string())

    return {"status": "sent", "to": user_email}
