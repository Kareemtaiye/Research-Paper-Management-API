# app/services/email_renderer.py
from jinja2 import Environment, FileSystemLoader, select_autoescape
import os

template_env = Environment(
    loader=FileSystemLoader(os.path.join(os.path.dirname(__file__), "../templates")),
    autoescape=select_autoescape(["html"]),
)


def render_email(template_name: str, context: dict) -> str:
    """Render an email template with given context."""
    template = template_env.get_template(f"emails/{template_name}")
    return template.render(**context)
