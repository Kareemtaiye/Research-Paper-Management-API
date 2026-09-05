import resend
from app.core.config import settings
from app.schemas import user
from app.services.email_renderer import render_email
from app.core.logger import logger

API_KEY = settings.resend_api_key
resend.api_key = API_KEY

frontend_url = (
    settings.frontend_url_prod
    if settings.is_production
    else settings.frontend_url_local
)


class EmailManager:
    def __init__(self):
        self.from_email = settings.from_email
        self.noreply_email = settings.noreply_email
        self.verify_email = settings.verify_email
        self.security_email = settings.security_email
        self.welcome_email = settings.welcome_email

        self.from_email_test = settings.from_email_test
        self.reply_to_email = settings.reply_to_email
        self.display_name = settings.display_name

        # send_feedback (to you)
        # "from": f"{DISPLAY_NAME} <{NOREPLY_EMAIL}>"
        # "to":   CONTACT_EMAIL   # your personal email

        # On feedback email specifically
        # resend.Emails.send({
        #     "from":     f"{DISPLAY_NAME} <{NOREPLY_EMAIL}>",
        #     "to":       CONTACT_EMAIL,
        #     "reply_to": body.email,   # reply goes to the user who submitted
        #     "subject":  subject,
        #     "html":     html
        # })

    def send(self, from_email: str, user_email: str, subject: str, html: str) -> dict:
        params = {
            "from": f"{self.display_name} <{from_email}>",
            "to": str(user_email),
            "reply_to": self.reply_to_email,
            "subject": subject,
            "html": html,
        }
        email = resend.Emails.send(params)
        return email

    def send_welcome_email(self, user_email: str, user_full_name: str | None):
        subject = "Welcome to PaperBase"
        hi = f"Hi {user_full_name or user_email.split('@')[0]},"
        html = render_email(
            "welcome.html",
            {
                "hi": hi,
                "support_email": self.reply_to_email,
            },
        )
        self.send(self.welcome_email, user_email, subject, html)
        logger.info(f"Welcome email sent to {user_email}.")

    def send_paper_complete_email(
        self, subject: str, user_email: str, user_full_name: str, paper: dict
    ):
        # In email templates
        hi = f"Hi {user_full_name or user_email.split('@')[0]},"
        html = render_email(
            "paper_completed.html",
            {
                "hi": hi,
                "title": paper["title"],
                "authors": ", ".join(paper["authors"] or []),
                "published_at": paper["published_at"],
                "categories": ", ".join(paper["categories"]) or "NIL",
                "abstract": paper["abstract"],
                "arxiv_url": paper["arxiv_url"],
            },
        )
        # Logic to send email (e.g., using an email service or SMTP)
        self.send(self.noreply_email, user_email, subject, html)
        logger.info(
            f"Email sent to {user_email} about paper '{paper['title']}' completion."
        )

    def send_password_reset_email(self, user_email: str, token: str):
        subject = "Password Reset Request"
        reset_link = f"{frontend_url}/reset-password?token={token}"
        html = render_email(
            "password_reset.html",
            {
                "reset_link": reset_link,
                "support_email": self.reply_to_email,
                "email": user_email,
            },
        )
        self.send(self.security_email, user_email, subject, html)
        logger.info(f"Password reset email sent to {user_email}.")

    def send_email_verification_email(self, user_email: str, token: str):
        subject = "Email Verification"
        verify_link = f"{frontend_url}/verify-email?token={token}"
        html = render_email(
            "email_verification.html",
            {
                "verify_link": verify_link,
                "support_email": self.reply_to_email,
                "email": user_email,
            },
        )
        self.send(self.verify_email, user_email, subject, html)
        logger.info(f"Email verification email sent to {user_email}.")

    def send_email_verification_success_email(self, user_email: str):
        subject = "Email Verified Successfully"
        html = render_email(
            "email_verified.html",
            {
                "support_email": self.reply_to_email,
            },
        )
        self.send(self.verify_email, user_email, subject, html)
        logger.info(f"Email verification success email sent to {user_email}.")

    def send_password_reset_success_email(self, user_email: str):
        subject = "Password Reset Successful"
        html = render_email(
            "password_reset_success.html",
            {
                "support_email": self.reply_to_email,
            },
        )
        self.send(self.security_email, user_email, subject, html)
        logger.info(f"Password reset success email sent to {user_email}.")
