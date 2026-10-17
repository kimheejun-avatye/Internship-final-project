# [확인하기] 요청 기록. IP별 시간당 횟수 계산에 쓴다

import uuid
from datetime import datetime

from sqlalchemy import DateTime, Index, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SignupCheckLog(Base):
    __tablename__ = "signup_check_log"
    __table_args__ = (Index("signup_check_log_ip_checked_at", "ip", "checked_at"),)

    log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    ip: Mapped[str] = mapped_column(Text, nullable=False)
    checked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
