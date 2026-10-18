from conftest import signin
from fastapi.testclient import TestClient

from app.db.session import SessionLocal
from app.main import app
from app.models import User


def test_idle_expiry_and_me_does_not_extend(client, seed, time):
    seed()
    r = signin(client)
    original = r.json()["idle_expires_at"]
    time.advance(minutes=29)
    from datetime import datetime

    assert datetime.fromisoformat(
        client.get("/api/auth/me").json()["idle_expires_at"]
    ) == datetime.fromisoformat(original)
    time.advance(minutes=1)
    assert client.get("/api/auth/me").status_code == 401
    assert client.post("/api/auth/activity", json={}).status_code == 401


def test_activity_and_absolute_expiry(client, seed, time):
    seed()
    signin(client)
    for _ in range(16):
        time.advance(minutes=29)
        assert client.post("/api/auth/activity", json={}).status_code == 200
    time.advance(minutes=15)
    r = client.post("/api/auth/activity", json={})
    assert r.status_code == 200
    assert r.json()["idle_expires_at"] == r.json()["absolute_expires_at"]
    time.advance(minutes=1)
    assert client.get("/api/auth/me").status_code == 401


def test_multiple_sessions_logout_only_current(client, seed):
    seed()
    signin(client)
    with TestClient(app, headers={"Origin": "http://127.0.0.1:5174"}) as other:
        signin(other)
        old = client.cookies.get("session")
        assert other.cookies.get("session") != old
        assert client.post("/api/auth/logout", json={}).status_code == 204
        assert other.get("/api/auth/me").status_code == 200
        client.cookies.set("session", old)
        assert client.get("/api/auth/me").status_code == 401
        assert client.post("/api/auth/logout", json={}).status_code == 204


def test_csrf_and_origin(client, seed):
    seed()
    signin(client)
    assert (
        client.post(
            "/api/auth/activity", json={}, headers={"X-CSRF-Token": "wrong"}
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/auth/logout", json={}, headers={"Origin": "https://evil.example"}
        ).status_code
        == 403
    )
    assert (
        client.post(
            "/api/auth/activity", content="{}", headers={"Content-Type": "text/plain"}
        ).status_code
        == 415
    )
    assert client.get("/api/auth/me").status_code == 200


def test_blocked_existing_session(client, seed):
    user_id = seed()
    signin(client)
    from app.services.clock import now

    with SessionLocal() as db:
        db.get(User, user_id).blocked_at = now()
        db.commit()
    assert client.get("/api/auth/me").json()["detail"]["code"] == "USER_BLOCKED"


def test_me_does_not_extend_even_with_user_activity_header(client, seed, time):
    seed()
    signin(client)
    time.advance(minutes=10)
    original = client.get("/api/auth/me").json()["idle_expires_at"]
    assert (
        client.get("/api/auth/me", headers={"X-Session-Activity": "user"}).json()[
            "idle_expires_at"
        ]
        == original
    )
