from uuid import UUID

from sqlalchemy import ForeignKey, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReservationAttendee(Base):
    __tablename__ = "reservation_attendees"

    reservation_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey(
            "reservations.reservation_id",
            ondelete="CASCADE",
        ),
        primary_key=True,
    )

    user_id: Mapped[UUID] = mapped_column(
        Uuid,
        ForeignKey("users.user_id"),
        primary_key=True,
        index=True,
    )
