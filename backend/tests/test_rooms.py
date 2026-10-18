import uuid
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.main import app
from app.models.rooms import Room, RoomStatus


def test_list_rooms_empty(client):
    response = client.get("/rooms")

    assert response.status_code == 200
    assert response.json() == []


def test_list_rooms_returns_saved_rooms(client):
    first_id = uuid.uuid4()
    second_id = uuid.uuid4()

    with SessionLocal() as db:
        db.add_all([
            Room(
                room_id=first_id,
                name="테스트 A회의실",
                status=RoomStatus.ACTIVE,
                capacity=6,
            ),
            Room(
                room_id=second_id,
                name="테스트 B회의실",
                status=RoomStatus.ACTIVE,
                capacity=10,
            ),
        ])
        db.commit()

    response = client.get("/rooms")

    assert response.status_code == 200

    data = response.json()
    assert len(data) == 2
    assert {
        "room_id": str(first_id),
        "name": "테스트 A회의실",
        "status": "ACTIVE",
        "capacity": 6,
    } in data
    assert {
        "room_id": str(second_id),
        "name": "테스트 B회의실",
        "status": "ACTIVE",
        "capacity": 10,
    } in data


def test_list_rooms_database_error_returns_500():
    failure = OperationalError(
        "SELECT rooms",
        {},
        RuntimeError("test database error"),
    )

    with patch.object(Session, "scalars", side_effect=failure) as query:
        with TestClient(app, raise_server_exceptions=False) as client:
            response = client.get("/rooms")

        query.assert_called()

    assert response.status_code == 500
