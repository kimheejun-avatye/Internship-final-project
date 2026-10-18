"""Integration boundary with the unchanged signup feature."""

from conftest import signin
from fastapi.testclient import TestClient
from test_auth import BASE, FORM, verified_token

from app.db.session import SessionLocal
from app.main import app
from app.models.users import User
from app.services import clock


def test_signup_approval_login_and_password_change(client, mails):
    token = verified_token(client, mails)
    response = client.post(BASE, json={**FORM, "signup_token": token})
    assert response.status_code == 201
    assert response.json()["status"] == "PENDING"
    assert (
        signin(client, FORM["email"], FORM["password"]).json()["detail"]["code"]
        == "USER_PENDING"
    )
    # Approval is an external feature; only simulate its existing DB contract here.
    from uuid import UUID

    with SessionLocal() as db:
        db.get(User, UUID(response.json()["user_id"])).approved_at = clock.now()
        db.commit()
    assert signin(client, FORM["email"], FORM["password"]).status_code == 200
    assert (
        client.post(
            "/api/auth/password/change",
            json={"current_password": FORM["password"], "new_password": "Changed123!"},
        ).status_code
        == 204
    )
    assert signin(client, FORM["email"], FORM["password"]).status_code == 401
    assert signin(client, FORM["email"], "Changed123!").status_code == 200


def test_signup_endpoint_does_not_inherit_login_origin_policy():
    with TestClient(app, client=("127.0.0.1", 50000)) as other:
        assert (
            other.post(
                BASE + "/check-email", json={"email": "unregistered@example.com"}
            ).status_code
            == 200
        )
