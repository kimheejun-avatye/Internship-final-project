"""Explicit operator CLI; never exposes account approval to unauthenticated HTTP clients."""

import argparse

from sqlalchemy import select

from app.db.session import SessionLocal
from app.models.users import User
from app.services.clock import now


def main():
    parser = argparse.ArgumentParser(description="Approve an existing signup")
    parser.add_argument("email")
    args = parser.parse_args()
    email = args.email.strip().lower()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.email == email).with_for_update())
        if user is None or user.blocked_at is not None:
            parser.error("An eligible pending account was not found")
        if user.approved_at is None:
            user.approved_at = now()
        db.commit()
    print("Account approved.")


if __name__ == "__main__":
    main()
