from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.rooms import RoomOut
from app.services.rooms import list_rooms

router = APIRouter()

@router.get("/rooms", response_model=list[RoomOut])
def get_rooms(db: Session = Depends(get_db)):
    return list_rooms(db)