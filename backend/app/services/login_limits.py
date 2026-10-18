import math
from datetime import timedelta

from sqlalchemy import delete, func, select, text

from app.core.exceptions import ApiError
from app.core.security import digest
from app.models.login_attempts import LoginFailure, LoginIPRequest, LoginLock
from app.services import clock


def lock(db, key):
    db.execute(
        text("SELECT pg_advisory_xact_lock(hashtextextended(:key, 0))"), {"key": key}
    )


def key_for(email):
    return digest("login-email", "", email)


def ip_limit(db, ip, scope="login"):
    key = digest("request-ip", scope, ip)
    lock(db, "ip:" + key)
    now = clock.now()
    count, oldest = db.execute(
        select(func.count(), func.min(LoginIPRequest.requested_at)).where(
            LoginIPRequest.ip_key == key,
            LoginIPRequest.requested_at > now - timedelta(minutes=1),
        )
    ).one()
    if count >= 30:
        db.rollback()
        raise ApiError(
            429,
            "IP_RATE_LIMITED",
            "요청이 많습니다. 잠시 후 다시 시도해주세요.",
            max(1, math.ceil((oldest + timedelta(minutes=1) - now).total_seconds())),
        )
    db.add(LoginIPRequest(ip_key=key, requested_at=now))
    db.commit()


def email_limit(db, email):
    key = key_for(email)
    lock(db, "login:" + key)
    row = db.get(LoginLock, key)
    now = clock.now()
    if row and row.blocked_until and row.blocked_until > now:
        raise ApiError(
            429,
            "LOGIN_RATE_LIMITED",
            "잠시 후 다시 로그인해주세요.",
            max(1, math.ceil((row.blocked_until - now).total_seconds())),
        )
    # An expired lock opens a fresh attempt window, rather than immediately relocking.
    if row and row.blocked_until:
        db.execute(delete(LoginFailure).where(LoginFailure.email_key == key))
        row.blocked_until = None
    if not row:
        row = LoginLock(email_key=key)
        db.add(row)
    return key, row


def failed(db, key, row):
    now = clock.now()
    db.add(LoginFailure(email_key=key, failed_at=now))
    db.flush()
    count = db.scalar(
        select(func.count())
        .select_from(LoginFailure)
        .where(
            LoginFailure.email_key == key,
            LoginFailure.failed_at > now - timedelta(minutes=15),
        )
    )
    if count >= 5:
        row.blocked_until = now + timedelta(minutes=5)
    db.commit()  # Expected authentication errors must preserve the failed attempt.
    if count >= 5:
        raise ApiError(
            429, "LOGIN_RATE_LIMITED", "로그인 시도 횟수를 초과했습니다.", 300
        )
    raise ApiError(401, "INVALID_CREDENTIALS", "이메일 또는 비밀번호를 확인해주세요.")


def clear(db, key, row):
    db.execute(delete(LoginFailure).where(LoginFailure.email_key == key))
    row.blocked_until = None
