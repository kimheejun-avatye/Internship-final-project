from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.rooms import Room

def list_rooms(db: Session):
    statement = select(Room)
    result = db.scalars(statement)
    rooms = result.all()
    return rooms