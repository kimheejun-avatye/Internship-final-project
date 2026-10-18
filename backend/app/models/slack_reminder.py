# app/models/slack_reminder.py
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from sqlalchemy import (
    DateTime,
    Enum as SAEnum,
    ForeignKeyConstraint,
    Index,
    Text,
    UniqueConstraint,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReminderStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SENT = "SENT"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


class SlackReminder(Base):
    __tablename__ = "slack_reminders"

    __table_args__ = (
        # 참석자 테이블의 복합 PK를 하나의 FK로 참조
        ForeignKeyConstraint(
            ["reservation_id", "user_id"],
            [
                "reservation_attendees.reservation_id",
                "reservation_attendees.user_id",
            ],
            name="fk_slack_reminders_attendee",
            ondelete="CASCADE",
        ),
        # 예약별 참석자 한 명당 알림 작업 한 건
        UniqueConstraint(
            "reservation_id",
            "user_id",
            name="uq_slack_reminders_attendee",
        ),
        # 발송 대기 상태와 예정 시각을 기준으로 조회
        Index(
            "ix_slack_reminders_status_scheduled",
            "status",
            "scheduled_at",
        ),
    )

    # 리마인더 ID
    reminder_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )

    # 복합 FK 구성 WHY? 참조하는 테이블(reservation_attendees)이 복합 PK
    reservation_id: Mapped[UUID] = mapped_column(
        Uuid,
        nullable=False,
    )

    # 복합 FK 구성 WHY? 참조하는 테이블(reservation_attendees)이 복합 PK
    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        nullable=False,
    )

    scheduled_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    slack_channel_id: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # 기본값 PENDING
    status: Mapped[ReminderStatus] = mapped_column(
        SAEnum(ReminderStatus, name="reminder_status"),
        nullable=False,
        default=ReminderStatus.PENDING,
        server_default=ReminderStatus.PENDING.value,
    )

    # 처리 시작 시각
    claimed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # 발송 완료 시각
    sent_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # 오류 내용
    last_error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    # 생성 시각
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
