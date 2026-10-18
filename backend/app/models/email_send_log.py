# 인증 메일 발송 기록. 이메일별·IP별·서비스 전체 횟수 계산에 쓴다

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Index, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class EmailSendLog(Base):
    __tablename__ = "email_send_log"
    __table_args__ = (
        Index("email_send_log_email_sent_at", "email", "sent_at"),
        Index("email_send_log_ip_sent_at", "ip", "sent_at"),
    )

    log_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )
    email: Mapped[str] = mapped_column(Text, nullable=False)
    ip: Mapped[str] = mapped_column(Text, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    # 서버 쪽 발송 실패(재시도 소진, 5xx)는 사용자 횟수에서 제외한다
    failed: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("false")
    )
