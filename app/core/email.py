import resend
from app.core.config import settings
from app.services.email_renderer import render_email
from app.core.logger import logger

API_KEY = settings.resend_api_key
resend.api_key = API_KEY


class EmailManager:
    def __init__(self):
        self.from_email = settings.from_email
        self.noreply_email = settings.noreply_email
        self.from_email_test = settings.from_email_test
        self.reply_to_email = settings.reply_to_email
        self.display_name = settings.display_name

    def send(self, user_email: str, subject: str, html: str) -> dict:
        params = {
            "from": f"{self.display_name} <{self.from_email}>",
            "to": str(user_email),
            "reply_to": self.reply_to_email,
            "subject": subject,
            "html": html,
        }
        email = resend.Emails.send(params)
        return email

    def send_paper_complete_email(self, subject: str, user_email: str, paper: dict):
        html = render_email(
            "paper_completed.html",
            {
                "title": paper["title"],
                "authors": ", ".join(paper["authors"] or []),
                "published_at": paper["published_at"],
                "categories": ", ".join(paper["categories"]) or "NIL",
                "abstract": paper["abstract"],
                "arxiv_url": paper["arxiv_url"],
            },
        )
        # Logic to send email (e.g., using an email service or SMTP)
        self.send(user_email, subject, html)
        logger.info(
            f"Email sent to {user_email} about paper '{paper['title']}' completion."
        )
