import secrets

from sqlalchemy import select

from app.core import security
from app.models.users import User
from app.services import login_limits, sessions

_DUMMY_HASH = security.hash_password(secrets.token_urlsafe(32))


def login(db, ip, email, password):
    key, limit = login_limits.email_limit(db, email)
    user = db.scalar(select(User).where(User.email == email).with_for_update())
    if (
        not security.verify_password(
            password, user.password_hash if user else _DUMMY_HASH
        )
        or user is None
    ):
        login_limits.failed(db, key, limit)
    sessions.allowed(user)
    login_limits.clear(db, key, limit)
    if security.check_needs_rehash(user.password_hash):
        user.password_hash = security.hash_password(password)
    token, session = sessions.create(db, user)
    db.commit()
    return token, sessions.payload(user, session)
