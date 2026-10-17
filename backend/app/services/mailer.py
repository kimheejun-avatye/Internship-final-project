# 인증 메일 발송. SMTP 4xx 는 지수 백오프 + 지터로 최대 3회 재시도, 5xx 는 즉시 실패

import logging
import random
import smtplib
import time
import uuid
from email.message import EmailMessage

from sqlalchemy import update

from app.core.config import settings
from app.db import session as db
from app.models.email_send_log import EmailSendLog

logger = logging.getLogger(__name__)

RETRY_DELAYS = (2, 4, 8)


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
        smtp.starttls()
        smtp.login(settings.smtp_user, settings.smtp_password)
        smtp.send_message(msg)


def _transient(exc: Exception) -> bool:
    if isinstance(exc, smtplib.SMTPResponseException):
        return 400 <= exc.smtp_code < 500
    return isinstance(exc, (smtplib.SMTPServerDisconnected, TimeoutError, ConnectionError))


def deliver_code(log_id: uuid.UUID, email: str, code: str) -> None:
    minutes = settings.code_ttl_seconds // 60
    subject = "[회의실 예약] 이메일 인증번호"
    body = f"인증번호: {code}\n{minutes}분 안에 입력해 주세요. 본인이 요청하지 않았다면 이 메일을 무시하세요."
    for attempt in range(len(RETRY_DELAYS) + 1):
        try:
            send_email(email, subject, body)
            return
        except Exception as exc:  # noqa: BLE001 - 어떤 실패든 횟수 제외 처리까지 가야 한다
            if _transient(exc) and attempt < len(RETRY_DELAYS):
                time.sleep(RETRY_DELAYS[attempt] * random.uniform(0.5, 1.5))
                continue
            logger.error("verification mail failed for log %s: %s", log_id, exc)
            break
    # 서버 쪽 실패는 사용자의 시간당 횟수에서 제외한다
    with db.SessionLocal() as session:
        session.execute(update(EmailSendLog).where(EmailSendLog.log_id == log_id).values(failed=True))
        session.commit()
