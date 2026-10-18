from datetime import timedelta

from app.core.security import digest
from app.db.session import SessionLocal
from app.models import EmailVerification
from app.services.clock import now


def payload():
    with SessionLocal() as db:
        db.add(
            EmailVerification(
                email="member@example.com",
                signup_token_hash=digest("token", "member@example.com", "signup-proof"),
                signup_token_expires_at=now() + timedelta(minutes=15),
            )
        )
        db.commit()
    return {
        "email": "member@example.com",
        "signup_token": "signup-proof",
        "password": "Example123!",
        "name": "테스트",
        "birth_date": "2000-01-01",
        "phone": "01012345678",
        "team": "AVATYE",
    }


def test_signup_pending_uuid_and_consumed(client):
    body = payload()
    r = client.post("/api/auth/signup", json=body)
    assert r.status_code == 201, r.text
    import uuid

    uuid.UUID(r.json()["user_id"])
    assert r.json()["status"] == "PENDING"
    assert client.post("/api/auth/signup", json=body).status_code == 400


def test_blocked_email_still_unique_and_proof_rolled_back(client, seed):
    seed(blocked=True)
    body = payload()
    r = client.post("/api/auth/signup", json=body)
    assert r.status_code == 409 and r.json()["detail"]["code"] == "EMAIL_ALREADY_EXISTS"
    with SessionLocal() as db:
        assert (
            db.get(EmailVerification, "member@example.com").signup_token_hash
            is not None
        )
