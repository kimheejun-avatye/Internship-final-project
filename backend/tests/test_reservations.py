"""예약 화면의 조회 조건을 별도 PostgreSQL 테스트 DB에서 검증한다."""

import os
from datetime import datetime, timedelta
from uuid import UUID
from zoneinfo import ZoneInfo

import pytest
from pydantic import ValidationError
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

from app.api.routes.reservation import ReservationController
from app.db.session import SessionLocal
from app.models.reservation_attendee import ReservationAttendee
from app.models.reservations import Reservation
from app.models.rooms import Room
from app.models.users import Team, User
from app.schemas.reservations import ReservationListOut, ReservationListQuery
from app.services import reservations as reservation_module
from app.services.reservations import ReservationService


@pytest.fixture
def now(monkeypatch):
    # 한국은 18일이지만 UTC는 17일인 시각으로 날짜 경계도 검증한다.
    fixed = datetime(2026, 10, 18, 0, 30, tzinfo=ZoneInfo("Asia/Seoul"))

    class FrozenDatetime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed.astimezone(tz) if tz else fixed.replace(tzinfo=None)

    monkeypatch.setattr(reservation_module, "datetime", FrozenDatetime)
    return fixed


@pytest.fixture
def db():
    with SessionLocal() as session:
        test_database = os.environ["POSTGRES_DB"]
        assert test_database.endswith("_test")
        assert session.scalar(text("SELECT current_database()")) == test_database
        yield session
        session.rollback()


@pytest.fixture
def sample(db):
    first_user = User(
        email="reservation-a@example.com", name="예약자 A",
        password_hash="unused", team=Team.AVATYE,
    )
    second_user = User(
        email="reservation-b@example.com", name="예약자 B",
        password_hash="unused", team=Team.GURU,
    )
    first_room = Room(name="테스트 A회의실", capacity=6)
    second_room = Room(name="테스트 B회의실", capacity=10)
    db.add_all([first_user, second_user, first_room, second_room])
    db.flush()
    return first_user, second_user, first_room, second_room


def add_reservation(db, room, user, start_at, end_at, reservation_id=None):
    reservation = Reservation(
        room_id=room.room_id,
        user_id=user.user_id,
        title="조회 테스트 예약",
        start_at=start_at,
        end_at=end_at,
        participants=0,
        created_at=start_at,
    )
    if reservation_id is not None:
        reservation.reservation_id = reservation_id
    db.add(reservation)
    db.flush()
    return reservation


def test_empty_room_returns_empty_page(db, sample, now):
    user, _, room, _ = sample

    result = ReservationService(db).get_my_today_reservations(user.user_id, room.room_id)

    assert result.items == []
    assert (result.total, result.page, result.page_size) == (0, 1, 5)


@pytest.mark.parametrize(
    "start_minutes,end_minutes,included",
    [
        (-90, -30, False),  # 오늘 00:00에 종료
        (-20, -1, False),  # 이미 종료
        (-20, 0, False),  # 조회 시각에 정확히 종료
        (-20, 20, True),  # 진행 중
        (-60, 10, True),  # 어제 시작했지만 아직 진행 중
        (60, 90, True),  # 오늘 시작할 예정
        (1380, 1500, True),  # 오늘 시작해서 내일 종료
        (1410, 1470, False),  # 내일 00:00에 시작
    ],
    ids=["midnight-end", "expired", "ends-now", "ongoing", "overnight",
         "future-today", "ends-tomorrow", "starts-tomorrow"],
)
def test_today_and_expiration_boundaries(db, sample, now, start_minutes, end_minutes, included):
    user, _, room, _ = sample
    reservation = add_reservation(
        db, room, user,
        now + timedelta(minutes=start_minutes),
        now + timedelta(minutes=end_minutes),
    )

    result = ReservationService(db).get_my_today_reservations(user.user_id, room.room_id)

    assert result.total == int(included)
    assert [item.reservation_id for item in result.items] == (
        [reservation.reservation_id] if included else []
    )


def test_room_filter_includes_other_organizers(db, sample, now):
    user, other_user, room, other_room = sample
    start, end = now + timedelta(hours=1), now + timedelta(hours=2)
    own = add_reservation(db, room, user, start, end)
    other = add_reservation(db, room, other_user, start, end)
    add_reservation(db, other_room, user, start, end)
    add_reservation(db, room, user, now - timedelta(hours=1), now)
    add_reservation(db, room, user, now + timedelta(days=1), now + timedelta(days=1, hours=1))

    result = ReservationService(db).get_my_today_reservations(user.user_id, room.room_id)

    assert result.total == 2
    assert {item.reservation_id for item in result.items} == {own.reservation_id, other.reservation_id}
    assert {item.room_id for item in result.items} == {room.room_id}


def test_pages_have_stable_order_and_filtered_total(db, sample, now):
    user, _, room, other_room = sample
    # 삽입 순서와 시작 시각/UUID 정렬 순서를 다르게 만든다.
    for number in [8, 6, 9, 5, 4, 3, 2, 1]:
        minutes = 60 if number == 9 else 180 if number == 8 else 120
        start = now + timedelta(minutes=minutes)
        add_reservation(db, room, user, start, start + timedelta(minutes=30), UUID(int=number))
    add_reservation(db, other_room, user, now, now + timedelta(hours=1))
    add_reservation(db, room, user, now - timedelta(hours=1), now)
    service = ReservationService(db)

    pages = [service.get_my_today_reservations(user.user_id, room.room_id, page) for page in (1, 2, 3)]

    expected = [[9, 1, 2, 3, 4], [5, 6, 8], []]
    for page_number, (result, numbers) in enumerate(zip(pages, expected), start=1):
        assert [item.reservation_id for item in result.items] == [UUID(int=n) for n in numbers]
        assert (result.total, result.page, result.page_size) == (8, page_number, 5)


def test_response_uses_attendee_counts_and_organizer_teams(db, sample, now):
    user, other_user, room, _ = sample
    reservations = [
        add_reservation(db, room, organizer, now, now + timedelta(hours=1))
        for organizer in (user, other_user, other_user)
    ]
    db.add_all([
        ReservationAttendee(reservation_id=reservations[1].reservation_id, user_id=user.user_id),
        ReservationAttendee(reservation_id=reservations[2].reservation_id, user_id=user.user_id),
        ReservationAttendee(reservation_id=reservations[2].reservation_id, user_id=other_user.user_id),
    ])
    db.flush()

    result = ReservationService(db).get_my_today_reservations(user.user_id, room.room_id)

    assert isinstance(result, ReservationListOut)
    assert result.total == 3
    items = {item.reservation_id: item for item in result.items}
    for reservation, count, team in zip(reservations, (0, 1, 2), (Team.AVATYE, Team.GURU, Team.GURU)):
        item = items[reservation.reservation_id]
        assert item.participant_count == count
        assert item.team == team
        assert item.room_id == room.room_id
        assert item.user_id == reservation.user_id
        assert item.title == reservation.title
        assert (item.start_at, item.end_at) == (reservation.start_at, reservation.end_at)
    payload = result.model_dump(mode="json")
    assert {item["team"] for item in payload["items"]} == {"AVATYE", "GURU"}


def test_controller_passes_query_to_real_database(db, sample, now):
    user, other_user, room, _ = sample
    for number in range(1, 7):
        add_reservation(db, room, other_user, now, now + timedelta(hours=1), UUID(int=number))
    controller = ReservationController(ReservationService(db))
    query = ReservationListQuery(room_id=str(room.room_id), page=2)

    result = controller.get_my_today_reservations(query=query, current_user=user)

    assert [item.reservation_id for item in result.items] == [UUID(int=6)]
    assert (result.total, result.page, result.page_size) == (6, 2, 5)


@pytest.mark.parametrize("page", [0, -1])
def test_query_rejects_invalid_page(sample, page):
    _, _, room, _ = sample
    with pytest.raises(ValidationError):
        ReservationListQuery(room_id=room.room_id, page=page)


def test_query_rejects_invalid_room_id():
    with pytest.raises(ValidationError):
        ReservationListQuery(room_id="not-a-uuid")


@pytest.mark.parametrize("page", [0, -1])
def test_service_rejects_invalid_page(db, sample, now, page):
    user, _, room, _ = sample
    with pytest.raises(ValueError, match="페이지 번호는 1 이상"):
        ReservationService(db).get_my_today_reservations(user.user_id, room.room_id, page)


def test_database_failure_is_not_returned_as_empty_success(db, sample, now, monkeypatch):
    user, _, room, _ = sample
    failure = OperationalError("SELECT reservations", {}, RuntimeError("test database error"))

    def fail_query(*args, **kwargs):
        raise failure

    monkeypatch.setattr(db, "scalar", fail_query)
    with pytest.raises(OperationalError):
        ReservationService(db).get_my_today_reservations(user.user_id, room.room_id)
