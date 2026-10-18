from conftest import PASSWORD, signin
from fastapi.testclient import TestClient
from sqlalchemy import func, select

from app.core.security import verify_password
from app.db.session import SessionLocal
from app.main import app
from app.models import EmailSendLog, PasswordResetVerification, User, UserSession
from app.services import mailer

NEW = "Changed123!"


def test_change_revokes_all(client, seed):
    seed()
    signin(client)
    with TestClient(app, headers={"Origin": "http://127.0.0.1:5174"}) as other:
        signin(other)
        assert (
            client.post(
                "/api/auth/password/change",
                json={"current_password": "bad", "new_password": NEW},
            ).status_code
            == 400
        )
        assert (
            client.post(
                "/api/auth/password/change",
                json={"current_password": PASSWORD, "new_password": "bad"},
            ).status_code
            == 422
        )
        assert (
            client.post(
                "/api/auth/password/change",
                json={"current_password": PASSWORD, "new_password": NEW},
            ).status_code
            == 204
        )
        assert other.get("/api/auth/me").status_code == 401
        assert signin(client).status_code == 401
        assert signin(client, password=NEW).status_code == 200


def proof(client, monkeypatch):
    captured = []
    monkeypatch.setattr(mailer, "send_email", lambda e, s, b: captured.append(b))
    assert (
        client.post(
            "/api/auth/password/reset/send-code", json={"email": "member@example.com"}
        ).status_code
        == 200
    )
    code = captured[0].split("인증번호: ")[1][:6]
    r = client.post(
        "/api/auth/password/reset/verify-code",
        json={"email": "member@example.com", "code": code},
    )
    assert r.status_code == 200, r.text
    return r.json()["reset_token"]


def test_reset_one_use_and_revokes(client, seed, monkeypatch):
    seed()
    signin(client)
    token = proof(client, monkeypatch)
    assert (
        client.post(
            "/api/auth/password/reset", json={"reset_token": token, "new_password": NEW}
        ).status_code
        == 204
    )
    assert client.get("/api/auth/me").status_code == 401
    assert (
        client.post(
            "/api/auth/password/reset", json={"reset_token": token, "new_password": NEW}
        ).status_code
        == 400
    )
    assert signin(client, password=NEW).status_code == 200


def test_reset_expires(client, seed, monkeypatch, time):
    seed()
    token = proof(client, monkeypatch)
    time.advance(minutes=15)
    assert (
        client.post(
            "/api/auth/password/reset", json={"reset_token": token, "new_password": NEW}
        ).status_code
        == 400
    )


def test_reset_send_failure_preserves_quota(client, seed, monkeypatch):
    from app.core.exceptions import ApiError

    seed()
    monkeypatch.setattr(
        mailer,
        "send_email",
        lambda *_: (_ for _ in ()).throw(ApiError(503, "MAIL_FAILED", "failed")),
    )
    assert (
        client.post(
            "/api/auth/password/reset/send-code", json={"email": "member@example.com"}
        ).status_code
        == 503
    )
    with SessionLocal() as db:
        assert db.scalar(select(func.count()).select_from(EmailSendLog)) == 0
        assert db.get(PasswordResetVerification, "member@example.com") is None


def test_reset_absent_same_send_response(client, seed, monkeypatch):
    seed()
    monkeypatch.setattr(mailer, "send_email", lambda *_: None)
    a = client.post(
        "/api/auth/password/reset/send-code", json={"email": "member@example.com"}
    )
    b = client.post(
        "/api/auth/password/reset/send-code", json={"email": "missing@example.com"}
    )
    assert a.json() == b.json()


def test_wrong_reset_code_locks(client, seed, monkeypatch):
    seed()
    monkeypatch.setattr(mailer, "send_email", lambda *_: None)
    client.post(
        "/api/auth/password/reset/send-code", json={"email": "member@example.com"}
    )
    for _ in range(5):
        assert (
            client.post(
                "/api/auth/password/reset/verify-code",
                json={"email": "member@example.com", "code": "------"},
            ).status_code
            == 422
        )
    for _ in range(5):
        assert (
            client.post(
                "/api/auth/password/reset/verify-code",
                json={"email": "member@example.com", "code": "000000"},
            ).status_code
            == 400
        )
    assert (
        client.post(
            "/api/auth/password/reset/verify-code",
            json={"email": "member@example.com", "code": "000000"},
        ).status_code
        == 429
    )


def test_change_rolls_back_if_revoke_fails(client, seed, monkeypatch):
    from sqlalchemy.exc import OperationalError

    from app.services import sessions

    seed()
    signin(client)
    monkeypatch.setattr(
        sessions,
        "revoke_all",
        lambda *_: (_ for _ in ()).throw(
            OperationalError("test", {}, Exception("injected"))
        ),
    )
    assert (
        client.post(
            "/api/auth/password/change",
            json={"current_password": PASSWORD, "new_password": NEW},
        ).status_code
        == 503
    )
    with SessionLocal() as db:
        assert verify_password(PASSWORD, db.scalar(select(User)).password_hash)
        assert db.scalar(select(UserSession)).revoked_at is None


def test_reset_rollback_keeps_proof(client, seed, monkeypatch):
    from sqlalchemy.exc import OperationalError

    from app.services import sessions

    seed()
    signin(client)
    token = proof(client, monkeypatch)
    original = sessions.revoke_all
    monkeypatch.setattr(
        sessions,
        "revoke_all",
        lambda *_: (_ for _ in ()).throw(
            OperationalError("test", {}, Exception("injected"))
        ),
    )
    assert (
        client.post(
            "/api/auth/password/reset", json={"reset_token": token, "new_password": NEW}
        ).status_code
        == 503
    )
    with SessionLocal() as db:
        assert verify_password(PASSWORD, db.scalar(select(User)).password_hash)
        assert (
            db.get(PasswordResetVerification, "member@example.com").reset_token_hash
            is not None
        )
    monkeypatch.setattr(sessions, "revoke_all", original)
    assert (
        client.post(
            "/api/auth/password/reset", json={"reset_token": token, "new_password": NEW}
        ).status_code
        == 204
    )


def test_current_password_repeated_guessing_limited(client, seed):
    seed()
    signin(client)
    for i in range(5):
        r = client.post(
            "/api/auth/password/change",
            json={"current_password": "wrong", "new_password": NEW},
        )
        assert r.status_code == (429 if i == 4 else 400)
