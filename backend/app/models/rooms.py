from enum import Enum
from uuid import UUID, uuid4

from sqlalchemy import (
    CheckConstraint,
    Enum as SAEnum,
    Integer,
    Text,
    Uuid,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class RoomStatus(str, Enum):
    ACTIVE = "ACTIVE"
    BLOCK = "BLOCK"


class Room(Base):
    __tablename__ = "rooms"

    __table_args__ = (
        # 회의 참석자는 음수가 될 수 없음
        CheckConstraint(
            "capacity > 0",
            name="ck_rooms_capacity",
        ),
    )

    room_id: Mapped[UUID] = mapped_column(
        Uuid,
        primary_key=True,
        default=uuid4,
    )

    name: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    status: Mapped[RoomStatus] = mapped_column(
        SAEnum(RoomStatus, name="room_status"),
        nullable=False,
        default=RoomStatus.ACTIVE,
    )

    capacity: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )