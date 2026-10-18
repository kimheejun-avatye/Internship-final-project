import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, ForeignKey, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PasswordResetVerification(Base):
    __tablename__ = "password_reset_verifications"
    email: Mapped[str] = mapped_column(Text, primary_key=True)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.user_id")
    )
    code_hash: Mapped[Optional[str]] = mapped_column(Text)
    code_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    reset_token_hash: Mapped[Optional[str]] = mapped_column(Text, unique=True)
    reset_token_expires_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True)
    )
    consumed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
