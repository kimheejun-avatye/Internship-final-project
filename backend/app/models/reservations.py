from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    Uuid,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Reservation(Base):
    __tablename__ = "reservations"

    __table_args__ = (
        # 종료시각은 시작시각보다 빠를 수 없음
        CheckConstraint(
            "end_at > start_at",
            name="ck_reservations_time_order",
        ),
        # 참석자는 음수가 될 수 없음
        CheckConstraint(
            "participants IS NULL OR participants >= 0",
            name="ck_reservations_participants",
        ),
        # 인덱스
        Index(
            "ix_reservations_room_start",
            "room_id",
            "start_at",
        ),
    )

    reservation_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )

    room_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("rooms.room_id"),
        nullable=False,
    )

    # 예약 생성자
    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.user_id"),
        nullable=False,
        index=True,
    )

    title: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # 기존 ERD의 참석 인원수
    participants: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    start_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
    )

    end_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )