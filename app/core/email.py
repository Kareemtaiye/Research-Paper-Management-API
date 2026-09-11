from datetime import datetime
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import resend
from app.core.config import settings
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
        self.contact_email = settings.contact_email

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
        if settings.is_production:
            params = {
                "from": f"{self.display_name} <{from_email}>",
                "to": str(user_email),
                "reply_to": self.reply_to_email,
                "subject": subject,
                "html": html,
            }
            return resend.Emails.send(params)

        self._send_local(user_email, subject, html, from_email)
        return {"status": "sent", "to": user_email}

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

    def send_email_verification_email(
        self, user_email: str, token: str, full_name: str | None = None
    ):
        subject = "Email Verification"
        verify_link = f"{frontend_url}/verify-email?token={token}"
        html = render_email(
            "verify_email.html",
            {
                "verify_link": verify_link,
                "support_email": self.reply_to_email,
                "email": user_email,
                "full_name": full_name,
            },
        )
        self.send(self.verify_email, user_email, subject, html)
        logger.info(f"Email verification email sent to {user_email}.")

    def send_email_verification_success_email(
        self, user_email: str, full_name: str | None = None
    ):
        subject = "Email Verified Successfully"
        html = render_email(
            "email_verification_success.html",
            {
                "email": user_email,
                "full_name": full_name,
                "dashboard_url": f"{frontend_url}/",
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
                "email": user_email,
                "reset_at": datetime.utcnow().strftime("%B %d, %Y at %H:%M UTC"),
                "login_url": f"{frontend_url}/login",
            },
        )
        self.send(self.security_email, user_email, subject, html)
        logger.info(f"Password reset success email sent to {user_email}.")

    def send_feedback_email(self, user_email: str, type: str, message: str):
        subject = {
            "feedback": "📝 New Feedback — RPM",
            "bug": "Bug Report — RPM",
        }.get(type, " New Submission — RPM")
        self.send(
            self.from_email,
            self.contact_email,
            subject,
            f"""
               <h2>{subject}</h2>
               <p><strong>Type:</strong> {type}</p>
               <p><strong>From:</strong> {user_email or 'Anonymous'}</p>
               <hr>
               <p>{message}</p>
           """,
        )



    def _send_local(self, to: str, subject: str, html: str, from_email: str):
        """Helper for MailHog local sending."""
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{self.display_name} <{from_email}>"
        msg["To"] = to
        msg["Reply-To"] = self.reply_to_email
        msg.attach(MIMEText(html, "html"))

        with smtplib.SMTP(
            settings.mail_hog_smtp_host, settings.mail_hog_smtp_port
        ) as server:
            server.sendmail(from_email, to, msg.as_string())