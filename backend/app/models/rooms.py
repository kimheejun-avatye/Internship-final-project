import uuid
import enum

from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import Text, Enum, Integer
from app.db.base import Base

class RoomStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    BLOCK = "BLOCK"


class Room(Base):
    __tablename__ = "rooms"
    room_id: Mapped[uuid.UUID] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[RoomStatus] = mapped_column(Enum(RoomStatus, name="room_status"), nullable=False)
    capacity: Mapped[int] = mapped_column(Integer, nullable=False)
