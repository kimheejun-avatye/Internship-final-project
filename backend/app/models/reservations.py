from pydantic import BaseModel


class reservationReadRequest(BaseModel):
    reservation_id: str
