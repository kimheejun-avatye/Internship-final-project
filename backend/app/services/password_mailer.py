import logging
import smtplib
import ssl
from email.message import EmailMessage

from app.core.config import settings

logger = logging.getLogger(__name__)


def send_email(to: str, subject: str, body: str) -> None:
    if not settings.smtp_user:
        # SMTP 를 설정하지 않은 로컬 개발에서는 콘솔에 남긴다
        logger.warning("SMTP not configured. mail to %s: %s | %s", to, subject, body)
        return
    msg = EmailMessage()
    msg["From"] = settings.smtp_user
    msg["To"] = to
    msg["Subject"] = subject
    msg.set_content(body)
    with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=10) as smtp:
        smtp.starttls(context=ssl.create_default_context())
        smtp.login(settings.smtp_user, settings.smtp_password)
        if smtp.send_message(msg):
            raise smtplib.SMTPRecipientsRefused({to: (550, "recipient refused")})
