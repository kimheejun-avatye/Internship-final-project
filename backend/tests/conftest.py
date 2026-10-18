import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / ".env")
os.environ.setdefault("SECRET_KEY", "test-secret")
# 개발 DB 를 건드리지 않도록 별도 DB 를 쓴다. app 을 import 하기 전에 바꿔야 한다
TEST_DB = os.environ["POSTGRES_DB"] + "_test"

import psycopg  # noqa: E402

with psycopg.connect(
    dbname="postgres",
    user=os.environ["POSTGRES_USER"],
    password=os.environ["POSTGRES_PASSWORD"],
    host="127.0.0.1",
    port=os.environ["POSTGRES_PORT"],
    autocommit=True,
) as conn:
    if not conn.execute("SELECT 1 FROM pg_database WHERE datname = %s", (TEST_DB,)).fetchone():
        conn.execute(f'CREATE DATABASE "{TEST_DB}"')
os.environ["POSTGRES_DB"] = TEST_DB

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import text  # noqa: E402

from app.db.base import Base  # noqa: E402
from app.db.session import engine  # noqa: E402
from app.main import app  # noqa: E402
import app.models as _models  # noqa: E402,F401
from app.models.reservations import Reservation  # noqa: E402,F401
from app.models.reservation_attendee import ReservationAttendee  # noqa: E402,F401
from app.services import mailer  # noqa: E402


@pytest.fixture(scope="session", autouse=True)
def schema():
    if engine.url.database != TEST_DB or not TEST_DB.endswith("_test"):
        raise RuntimeError("Refusing to reset non-test database")

    with engine.begin() as c:
        c.execute(text("DROP SCHEMA public CASCADE; CREATE SCHEMA public"))
    Base.metadata.create_all(engine)


@pytest.fixture(autouse=True)
def clean():
    yield
    with engine.begin() as c:
        c.execute(text(
            "TRUNCATE room_blocks, reservation_attendees, reservations, rooms, users, email_verifications, "
            "email_send_log, signup_check_log"
        ))


@pytest.fixture
def mails(monkeypatch):
    sent = []
    monkeypatch.setattr(mailer, "send_email", lambda to, subject, body: sent.append((to, body)))
    monkeypatch.setattr(mailer.time, "sleep", lambda s: None)
    return sent


@pytest.fixture
def client():
    return TestClient(app, client=("127.0.0.1", 50000))
