# 이메일 인증 모델 (이메일당 1행)

from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EmailVerification(Base):
    __tablename__ = "email_verifications"

    # 정규화한 이메일(앞뒤 공백 제거, 소문자)
    email: Mapped[str] = mapped_column(Text, primary_key=True)
    code_hash: Mapped[Optional[str]] = mapped_column(Text)
    code_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    last_sent_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    # 재전송해도 초기화하지 않는다
    failed_count: Mapped[int] = mapped_column(Integer, nullable=False, server_default="0")
    locked_until: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    signup_token_hash: Mapped[Optional[str]] = mapped_column(Text)
    signup_token_expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
