"""Delete expired auth records older than 30 days: python -m app.maintenance."""

from datetime import timedelta

from sqlalchemy import delete, or_

from app.db.session import SessionLocal
from app.models import (
    LoginFailure,
    LoginIPRequest,
    PasswordResetVerification,
    UserSession,
)
from app.services.clock import now


def cleanup():
    cutoff = now() - timedelta(days=30)
    with SessionLocal() as db:
        for model, condition in (
            (
                UserSession,
                or_(
                    UserSession.absolute_expires_at < cutoff,
                    UserSession.revoked_at < cutoff,
                ),
            ),
            (LoginFailure, LoginFailure.failed_at < cutoff),
            (LoginIPRequest, LoginIPRequest.requested_at < cutoff),
            (
                PasswordResetVerification,
                PasswordResetVerification.code_expires_at < cutoff,
            ),
        ):
            db.execute(delete(model).where(condition))
        db.commit()


if __name__ == "__main__":
    cleanup()
