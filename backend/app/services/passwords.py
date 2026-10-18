import smtplib
from datetime import timedelta

from sqlalchemy import func, select

from app.core import security
from app.core.config import settings
from app.core.exceptions import ApiError
from app.models.email_send_log import EmailSendLog
from app.models.password_reset_verifications import PasswordResetVerification as Reset
from app.models.users import User
from app.services import clock, login_limits, password_mailer, sessions


def change(db, user, current_password, new_password):
    # authenticated dependency holds the user lock, shared with login/reset.
    key, limit = login_limits.email_limit(db, "password-change:" + user.email)
    if not security.verify_password(current_password, user.password_hash):
        try:
            login_limits.failed(db, key, limit)
        except ApiError as exc:
            if exc.status_code == 401:
                raise ApiError(
                    400,
                    "CURRENT_PASSWORD_MISMATCH",
                    "현재 비밀번호가 올바르지 않습니다.",
                ) from exc
            raise
    login_limits.clear(db, key, limit)
    user.password_hash = security.hash_password(new_password)
    sessions.revoke_all(db, user.user_id)
    db.commit()


def send_code(db, ip, email):
    login_limits.ip_limit(db, ip, "password-reset-send")
    login_limits.lock(db, "reset:" + email)
    login_limits.lock(db, "email:" + email)  # Share email quota lock with signup.
    login_limits.lock(db, "send:global")
    now = clock.now()
    row = db.get(Reset, email)
    if row and row.locked_until and row.locked_until > now:
        raise ApiError(
            429,
            "CODE_LOCKED",
            "잠시 후 다시 시도해주세요.",
            max(1, int((row.locked_until - now).total_seconds())),
        )
    records = list(
        db.scalars(
            select(EmailSendLog).where(
                EmailSendLog.email == email,
                EmailSendLog.failed.is_(False),
                EmailSendLog.sent_at > now - timedelta(hours=1),
            )
        )
    )
    if records:
        wait = (
            max(x.sent_at for x in records)
            + timedelta(seconds=settings.resend_cooldown_seconds)
            - now
        ).total_seconds()
        if wait > 0:
            raise ApiError(
                429,
                "RESEND_COOLDOWN",
                "잠시 후 다시 요청해주세요.",
                max(1, int(wait + 1)),
            )
    if len(records) >= settings.email_hourly_limit:
        raise ApiError(
            429, "RATE_LIMIT_EMAIL", "인증번호 요청 횟수를 초과했습니다.", 3600
        )
    for filters, window, maximum in (
        ([EmailSendLog.ip == ip], timedelta(minutes=1), settings.ip_minute_send_limit),
        ([EmailSendLog.ip == ip], timedelta(hours=1), settings.ip_hourly_send_limit),
        ([], timedelta(days=1), settings.service_daily_send_limit),
    ):
        count = db.scalar(
            select(func.count())
            .select_from(EmailSendLog)
            .where(EmailSendLog.sent_at > now - window, *filters)
        )
        if count >= maximum:
            raise ApiError(
                429,
                "MAIL_RATE_LIMITED",
                "인증 메일 요청이 많습니다.",
                int(window.total_seconds()),
            )
    user = db.scalar(select(User).where(User.email == email, User.blocked_at.is_(None)))
    code = security.new_code()
    if user and user.blocked_at is None:
        # SMTP failure rolls the transaction back, preserving prior proof and quota.
        try:
            password_mailer.send_email(
                email,
                "[회의실 예약] 비밀번호 재설정",
                f"인증번호: {code}\n{settings.code_ttl_seconds // 60}분 안에 입력해주세요.",
            )
        except (OSError, smtplib.SMTPException) as exc:
            raise ApiError(
                503, "MAIL_FAILED", "메일을 보내지 못했습니다. 다시 시도해주세요."
            ) from exc
    if not row:
        row = Reset(email=email, failed_count=0)
        db.add(row)
    row.user_id = user.user_id if user and user.blocked_at is None else None
    row.code_hash = security.digest("reset-code", email, code)
    row.code_expires_at = now + timedelta(seconds=settings.code_ttl_seconds)
    row.reset_token_hash = None
    row.reset_token_expires_at = None
    row.consumed_at = None
    if row.locked_until and row.locked_until <= now:
        row.failed_count = 0
        row.locked_until = None
    db.add(EmailSendLog(email=email, ip=ip, sent_at=now, failed=False))
    db.commit()
    return {
        "message": "가입된 이메일이라면 인증번호를 발송했습니다.",
        "cooldown_seconds": settings.resend_cooldown_seconds,
        "expires_in": settings.code_ttl_seconds,
    }


def verify_code(db, ip, email, code):
    login_limits.ip_limit(db, ip, "password-reset-verify")
    login_limits.lock(db, "reset:" + email)
    row = db.get(Reset, email)
    now = clock.now()
    if row and row.locked_until and row.locked_until > now:
        raise ApiError(
            429,
            "CODE_LOCKED",
            "인증 시도 횟수를 초과했습니다.",
            max(1, int((row.locked_until - now).total_seconds())),
        )
    if not row or not row.code_hash or row.code_expires_at <= now:
        raise ApiError(400, "CODE_EXPIRED", "인증이 만료되었습니다. 다시 요청해주세요.")
    if (
        not security.same(row.code_hash, security.digest("reset-code", email, code))
        or row.user_id is None
    ):
        row.failed_count += 1
        if row.failed_count >= 5:
            row.locked_until = now + timedelta(minutes=15)
            row.code_hash = None
        db.commit()
        raise ApiError(
            400,
            "CODE_MISMATCH",
            "인증번호가 올바르지 않습니다.",
            remaining_attempts=max(0, 5 - row.failed_count),
        )
    token = security.new_signup_token()
    row.code_hash = None
    row.failed_count = 0
    row.reset_token_hash = security.digest("reset-token", "", token)
    row.reset_token_expires_at = now + timedelta(seconds=900)
    db.commit()
    return {"reset_token": token, "expires_in": 900}


def reset(db, ip, token, new_password):
    login_limits.ip_limit(db, ip, "password-reset-complete")
    hashed = security.digest("reset-token", "", token)
    found = db.scalar(select(Reset).where(Reset.reset_token_hash == hashed))
    if not found:
        raise ApiError(400, "INVALID_RESET_TOKEN", "인증이 없거나 만료되었습니다.")
    login_limits.lock(db, "reset:" + found.email)
    row = db.scalar(
        select(Reset)
        .where(Reset.email == found.email)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if (
        not row.reset_token_hash
        or not security.same(row.reset_token_hash, hashed)
        or not row.reset_token_expires_at
        or row.reset_token_expires_at <= clock.now()
        or row.consumed_at
    ):
        raise ApiError(400, "INVALID_RESET_TOKEN", "인증이 없거나 만료되었습니다.")
    user = db.scalar(
        select(User)
        .where(User.user_id == row.user_id)
        .with_for_update()
        .execution_options(populate_existing=True)
    )
    if not user or user.email != row.email or user.blocked_at is not None:
        raise ApiError(400, "INVALID_RESET_TOKEN", "인증이 없거나 만료되었습니다.")
    user.password_hash = security.hash_password(new_password)
    row.consumed_at = clock.now()
    row.reset_token_hash = None
    sessions.revoke_all(db, user.user_id)
    db.commit()
