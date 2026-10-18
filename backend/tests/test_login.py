from concurrent.futures import ThreadPoolExecutor

from conftest import signin
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core import security
from app.db.session import SessionLocal
from app.main import app
from app.models import LoginFailure, LoginIPRequest, LoginLock, UserSession


def test_login_cookie_and_me(client, seed):
    seed()
    r = signin(client, "  MEMBER@EXAMPLE.COM  ")
    assert r.status_code == 200
    cookie = r.headers["set-cookie"]
    assert "HttpOnly" in cookie and "SameSite=lax" in cookie and "Path=/" in cookie
    assert "password_hash" not in r.text
    assert client.get("/api/auth/me").json()["user"]["email"] == "member@example.com"
    with SessionLocal() as db:
        session = db.scalar(select(UserSession))
        assert session.token_hash != client.cookies.get("session")
        assert len(session.token_hash) == 64


def test_bad_credentials_and_lock(client, seed, time):
    seed()
    for i in range(5):
        r = signin(client, password="wrong")
        assert r.status_code == (429 if i == 4 else 401)
    with SessionLocal() as db:
        until = db.scalar(select(LoginLock)).blocked_until
    time.advance(minutes=1)
    assert signin(client).status_code == 429
    with SessionLocal() as db:
        assert db.scalar(select(LoginLock)).blocked_until == until
        assert db.scalar(select(func.count()).select_from(LoginFailure)) == 5
    time.advance(minutes=4)
    assert signin(client).status_code == 200


def test_rolling_window_and_success_clear(client, seed, time):
    seed()
    for _ in range(4):
        assert signin(client, password="wrong").status_code == 401
    time.advance(minutes=15)
    assert signin(client, password="wrong").status_code == 401
    assert signin(client).status_code == 200
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(LoginFailure)) == 0


def test_absent_email_same_error(client):
    assert (
        signin(client, password="wrong").json()["detail"]["code"]
        == "INVALID_CREDENTIALS"
    )


def test_pending_and_blocked(client, seed):
    seed(approved=False)
    assert signin(client).json()["detail"]["code"] == "USER_PENDING"
    assert not client.cookies.get("session")
    seed(email="blocked@example.com", blocked=True)
    assert (
        signin(client, email="blocked@example.com").json()["detail"]["code"]
        == "USER_BLOCKED"
    )
    assert (
        signin(client, email="blocked@example.com", password="wrong").status_code == 401
    )


def test_ip_rate_limit(client, time):
    for i in range(30):
        assert signin(client, email=f"missing{i}@example.com").status_code == 401
    r = signin(client, email="another@example.com")
    assert r.status_code == 429 and r.json()["detail"]["code"] == "IP_RATE_LIMITED"
    time.advance(seconds=60)
    assert signin(client, email="another@example.com").status_code == 401


def test_server_error_not_password_failure(client, seed, monkeypatch):
    from sqlalchemy.exc import OperationalError

    seed()
    monkeypatch.setattr(
        security,
        "verify_password",
        lambda *_: (_ for _ in ()).throw(
            OperationalError("test", {}, Exception("injected"))
        ),
    )
    assert signin(client).status_code == 503
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(LoginFailure)) == 0


def test_concurrent_failures(seed):
    seed()

    def attempt(_):
        with TestClient(app, headers={"Origin": "http://127.0.0.1:5174"}) as c:
            return signin(c, password="wrong").status_code

    with ThreadPoolExecutor(max_workers=6) as pool:
        statuses = list(pool.map(attempt, range(6)))
    assert sorted(statuses) == [401, 401, 401, 401, 429, 429]
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(LoginFailure)) == 5


def test_concurrent_ip_limit():
    def attempt(i):
        with TestClient(app, headers={"Origin": "http://127.0.0.1:5174"}) as c:
            return signin(c, email=f"missing{i}@example.com").status_code

    with ThreadPoolExecutor(max_workers=8) as pool:
        statuses = list(pool.map(attempt, range(32)))
    assert statuses.count(429) == 2
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(LoginIPRequest)) == 30


def test_invalid_login_bodies_count_ip_limit(client):
    for _ in range(30):
        assert client.post("/api/auth/login", json={}).status_code == 422
    assert signin(client).json()["detail"]["code"] == "IP_RATE_LIMITED"
