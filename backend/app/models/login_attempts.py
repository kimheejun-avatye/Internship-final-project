import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Index, Text, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class LoginFailure(Base):
    __tablename__ = "login_failures"
    __table_args__ = (Index("ix_login_failures_email_time", "email_key", "failed_at"),)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    email_key: Mapped[str] = mapped_column(Text, nullable=False)
    failed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)


class LoginLock(Base):
    __tablename__ = "login_locks"
    email_key: Mapped[str] = mapped_column(Text, primary_key=True)
    blocked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))


class LoginIPRequest(Base):
    __tablename__ = "login_ip_requests"
    __table_args__ = (Index("ix_login_ip_requests_key_time", "ip_key", "requested_at"),)
    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    ip_key: Mapped[str] = mapped_column(Text, nullable=False)
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
