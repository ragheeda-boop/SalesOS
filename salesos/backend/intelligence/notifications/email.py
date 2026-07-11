from __future__ import annotations

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

_TEMPLATES_DIR = Path(__file__).parent / "templates"


class EmailService:
    def __init__(
        self,
        smtp_host: str | None = None,
        smtp_port: int | None = None,
        smtp_user: str | None = None,
        smtp_password: str | None = None,
        smtp_from: str | None = None,
        use_ssl: bool = True,
    ):
        self._smtp_host = smtp_host or os.environ.get("SMTP_HOST", "")
        self._smtp_port = smtp_port or int(os.environ.get("SMTP_PORT", "465"))
        self._smtp_user = smtp_user or os.environ.get("SMTP_USER", "")
        self._smtp_password = smtp_password or os.environ.get("SMTP_PASSWORD", "")
        self._smtp_from = smtp_from or os.environ.get("SMTP_FROM", "noreply@salesos.io")
        self._use_ssl = use_ssl

    @property
    def configured(self) -> bool:
        return bool(self._smtp_host and self._smtp_user and self._smtp_password)

    def send(self, to: str, subject: str, body: str, html_body: str | None = None) -> bool:
        if not self.configured:
            logger.info("[EMAIL FALLBACK] To: %s | Subject: %s | Body: %s", to, subject, body[:200])
            return False

        msg = MIMEMultipart("alternative")
        msg["From"] = self._smtp_from
        msg["To"] = to
        msg["Subject"] = subject

        msg.attach(MIMEText(body, "plain"))
        if html_body:
            msg.attach(MIMEText(html_body, "html"))

        try:
            if self._use_ssl:
                with smtplib.SMTP_SSL(self._smtp_host, self._smtp_port) as server:
                    server.login(self._smtp_user, self._smtp_password)
                    server.send_message(msg)
            else:
                with smtplib.SMTP(self._smtp_host, self._smtp_port) as server:
                    server.starttls()
                    server.login(self._smtp_user, self._smtp_password)
                    server.send_message(msg)
            logger.info("Email sent to %s: %s", to, subject)
            return True
        except Exception:
            logger.exception("Failed to send email to %s: %s", to, subject)
            return False

    def send_template(self, to: str, template_name: str, context: dict[str, Any]) -> bool:
        template_path = _TEMPLATES_DIR / template_name
        if not template_path.exists():
            logger.warning("Template not found: %s", template_path)
            return self.send(to, "Notification", f"Template {template_name} not found", None)

        html_content = template_path.read_text(encoding="utf-8")
        rendered = self._render_template(html_content, context)
        plain_text = self._to_plain_text(rendered)

        subject_map = {
            "workflow_triggered.html": f"Workflow Executed: {context.get('workflow_name', 'N/A')}",
            "report_ready.html": f"Report Ready: {context.get('report_name', 'N/A')}",
            "nba_recommendation.html": f"NBA Recommendation: {context.get('action', 'N/A')}",
            "pipeline_stage_change.html": f"Deal Moved: {context.get('deal_name', 'N/A')} → {context.get('new_stage', 'N/A')}",
        }
        subject = subject_map.get(template_name, "Notification from SalesOS")

        return self.send(to, subject, plain_text, rendered)

    def send_to_many(self, recipients: list[str], subject: str, body: str, html_body: str | None = None) -> int:
        count = 0
        for to in recipients:
            if self.send(to, subject, body, html_body):
                count += 1
        return count

    @staticmethod
    def _render_template(template: str, context: dict[str, Any]) -> str:
        result = template
        for key, value in context.items():
            placeholder = "{{ " + key + " }}"
            placeholder_alt = "{{" + key + "}}"
            str_value = str(value)
            result = result.replace(placeholder, str_value).replace(placeholder_alt, str_value)
        result = result.replace('{{ "%.0f"|format(confidence * 100) }}', str(round(context.get("confidence", 0) * 100)))
        result = result.replace('{{ "%.2f"|format(value) }}', f"{context.get('value', 0):.2f}")
        return result

    @staticmethod
    def _to_plain_text(html: str) -> str:
        import re
        text = re.sub(r"<[^>]+>", "", html)
        text = re.sub(r"\n\s*\n", "\n\n", text)
        return text.strip()
