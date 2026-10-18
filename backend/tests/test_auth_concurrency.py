from concurrent.futures import ThreadPoolExecutor
from threading import Event

from conftest import PASSWORD, signin
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core import security
from app.db.session import SessionLocal
from app.main import app
from app.models import User, UserSession

ORIGIN = {"Origin": "http://127.0.0.1:5174"}


def test_login_started_before_password_change_is_revoked(client, seed, monkeypatch):
    seed()
    signin(client)
    entered, release = Event(), Event()
    original = security.verify_password

    def delayed(password, hashed):
        if not entered.is_set():
            entered.set()
            assert release.wait(5)
        return original(password, hashed)

    monkeypatch.setattr(security, "verify_password", delayed)

    def login():
        with TestClient(app, headers=ORIGIN) as other:
            r = signin(other)
            return r.status_code, other.cookies.get("session")

    with ThreadPoolExecutor(max_workers=2) as pool:
        pending = pool.submit(login)
        assert entered.wait(5)
        changed = pool.submit(
            client.post,
            "/api/auth/password/change",
            json={"current_password": PASSWORD, "new_password": "Changed123!"},
        )
        release.set()
        status, token = pending.result(timeout=10)
        assert status == 200
        assert changed.result(timeout=10).status_code == 204
    with TestClient(app, headers=ORIGIN) as other:
        other.cookies.set("session", token)
        assert other.get("/api/auth/me").status_code == 401
    with SessionLocal() as db:
        assert (
            db.scalar(
                select(func.count())
                .select_from(UserSession)
                .where(UserSession.revoked_at.is_(None))
            )
            == 0
        )


def test_logout_and_activity_never_revive(client, seed):
    seed()
    signin(client)
    token = client.cookies.get("session")
    csrf = client.headers["X-CSRF-Token"]

    def call(path):
        with TestClient(app, headers={**ORIGIN, "X-CSRF-Token": csrf}) as other:
            other.cookies.set("session", token)
            return other.post(path, json={}).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        a = pool.submit(call, "/api/auth/activity")
        b = pool.submit(call, "/api/auth/logout")
        assert a.result(timeout=10) in (200, 401)
        assert b.result(timeout=10) == 204
    assert client.get("/api/auth/me").status_code == 401


def test_concurrent_signup_consumes_proof_once(client):
    from test_signup import payload

    body = payload()

    def call(_):
        with TestClient(app, headers=ORIGIN, client=("127.0.0.1", 50000)) as other:
            return other.post("/api/auth/signup", json=body).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(call, range(2))) == [201, 400]
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(User)) == 1
