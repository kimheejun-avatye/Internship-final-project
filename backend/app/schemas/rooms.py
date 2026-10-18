import uuid
from pydantic import BaseModel, ConfigDict
from app.models.rooms import RoomStatus

class RoomOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    room_id: uuid.UUID
    name: str
    status: RoomStatus
    capacity: int