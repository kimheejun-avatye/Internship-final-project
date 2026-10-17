import re
import smtplib
from datetime import timedelta

import pytest
from sqlalchemy import text

from app.core.config import settings
from app.db.session import engine
from app.services import mailer

BASE = "/api/auth/signup"
EMAIL = "kim@example.com"
FORM = {
    "email": EMAIL,
    "password": "Passw0rd!x",
    "name": "김철수",
    "birth_date": "1995-03-02",
    "phone": "010-1234-5678",
    "team": "GURU",
}


def sql(query, **params):
    with engine.begin() as c:
        return c.execute(text(query), params)


def send(client, mails, email=EMAIL):
    r = client.post(f"{BASE}/send-code", json={"email": email}) # {"email": "kim@example.com"}을 JSON으로 POST /api/auth/signup/send-code에 보냅니다.
    assert r.status_code == 200, r.text                         # 200 아니면 응답 본문과 함께 실패
    return re.search(r"\d{6}", mails[-1][1]).group()            # 보낸 메일에서 6자리 숫자 추출하여 반환


def verified_token(client, mails, email=EMAIL):
    code = send(client, mails, email)
    r = client.post(f"{BASE}/verify-code", json={"email": email, "code": code}) # {"email": "kim@example.com", "code": "123456"}을 JSON으로 POST /api/auth/signup/verify-code에 보냅니다.
    assert r.status_code == 200, r.text                         # 200 아니면 응답 본문과 함께 실패
    return r.json()["signup_token"]     # 인증 토큰 반환


def expire_cooldown():
    sql("UPDATE email_send_log SET sent_at = sent_at - interval '61 seconds'")


def test_full_signup_creates_pending_user(client, mails):
    token = verified_token(client, mails, "  Kim@Example.com ")
    r = client.post(BASE, json={**FORM, "signup_token": token})
    assert r.status_code == 201 and r.json()["status"] == "PENDING"
    row = sql("SELECT email, phone, role, approved_at, password_hash FROM users").one()
    assert row.email == EMAIL and row.phone == "01012345678" and row.role == "MEMBER"
    assert row.approved_at is None and row.password_hash.startswith("$argon2id$")
    assert client.post(f"{BASE}/check-email", json={"email": EMAIL}).json() == {"status": "PENDING"}


def test_signup_token_is_one_time_and_email_bound(client, mails):
    token = verified_token(client, mails)
    other = {**FORM, "email": "lee@example.com", "signup_token": token}
    assert client.post(BASE, json=other).json()["detail"]["code"] == "INVALID_TOKEN"
    assert client.post(BASE, json={**FORM, "signup_token": token}).status_code == 201
    assert client.post(BASE, json={**FORM, "signup_token": token}).status_code == 400


def test_signup_without_verification_rejected(client):
    r = client.post(BASE, json={**FORM, "signup_token": "x" * 40})
    assert r.status_code == 400 and r.json()["detail"]["code"] == "INVALID_TOKEN"


def test_expired_signup_token(client, mails):
    token = verified_token(client, mails)
    sql("UPDATE email_verifications SET signup_token_expires_at = now() - interval '1 second'")
    assert client.post(BASE, json={**FORM, "signup_token": token}).status_code == 400


def test_resend_invalidates_old_code_and_token(client, mails):
    old = send(client, mails)
    expire_cooldown()
    send(client, mails)
    r = client.post(f"{BASE}/verify-code", json={"email": EMAIL, "code": old})
    assert r.status_code == 400 and r.json()["detail"]["code"] == "CODE_MISMATCH"


def test_code_is_one_time(client, mails):
    code = send(client, mails)
    assert client.post(f"{BASE}/verify-code", json={"email": EMAIL, "code": code}).status_code == 200
    r = client.post(f"{BASE}/verify-code", json={"email": EMAIL, "code": code})
    assert r.json()["detail"]["code"] == "CODE_EXPIRED"


def test_expired_code(client, mails):
    code = send(client, mails)
    sql("UPDATE email_verifications SET code_expires_at = now() - interval '1 second'")
    r = client.post(f"{BASE}/verify-code", json={"email": EMAIL, "code": code})
    assert r.json()["detail"]["code"] == "CODE_EXPIRED"


def test_five_failures_lock_and_resend_is_blocked(client, mails):
    code = send(client, mails)
    wrong = "000000" if code != "000000" else "111111"
    for i in range(4):
        r = client.post(f"{BASE}/verify-code", json={"email": EMAIL, "code": wrong})
        assert r.json()["detail"]["remaining_attempts"] == 4 - i
    r = client.post(f"{BASE}/verify-code", json={"email": EMAIL, "code": wrong})
    assert r.status_code == 429 and r.json()["detail"]["retry_after"] == settings.lock_seconds
    # 잠금 중에는 맞는 코드도, 재전송도 막힌다
    assert client.post(f"{BASE}/verify-code", json={"email": EMAIL, "code": code}).status_code == 429
    expire_cooldown()
    assert client.post(f"{BASE}/send-code", json={"email": EMAIL}).status_code == 429


def test_failed_count_survives_resend(client, mails):
    code = send(client, mails)
    wrong = "000000" if code != "000000" else "111111"
    for _ in range(3):
        client.post(f"{BASE}/verify-code", json={"email": EMAIL, "code": wrong})
    expire_cooldown()
    code = send(client, mails)
    assert sql("SELECT failed_count FROM email_verifications").scalar() == 3
    assert code


def test_resend_cooldown(client, mails):
    send(client, mails)
    r = client.post(f"{BASE}/send-code", json={"email": EMAIL})
    assert r.status_code == 429 and r.json()["detail"]["code"] == "RESEND_COOLDOWN"
    assert 0 < int(r.headers["Retry-After"]) <= 60


def test_hourly_limit_per_email_excludes_server_failures(client, mails):
    for _ in range(5):
        send(client, mails)
        expire_cooldown()
    r = client.post(f"{BASE}/send-code", json={"email": EMAIL})
    assert r.status_code == 429 and r.json()["detail"]["code"] == "RATE_LIMIT_EMAIL"
    # 서버 쪽 실패 한 건은 횟수에서 빠진다
    sql("UPDATE email_send_log SET failed = true WHERE log_id = (SELECT log_id FROM email_send_log LIMIT 1)")
    assert client.post(f"{BASE}/send-code", json={"email": EMAIL}).status_code == 200


def test_ip_and_service_limits(client, mails, monkeypatch):
    monkeypatch.setattr(settings, "ip_minute_send_limit", 2)
    send(client, mails, "a@example.com")
    send(client, mails, "b@example.com")
    r = client.post(f"{BASE}/send-code", json={"email": "c@example.com"})
    assert r.json()["detail"]["code"] == "RATE_LIMIT_IP"
    monkeypatch.setattr(settings, "ip_minute_send_limit", 20)
    monkeypatch.setattr(settings, "service_daily_send_limit", 2)
    r = client.post(f"{BASE}/send-code", json={"email": "c@example.com"})
    assert r.status_code == 429 and r.json()["detail"]["code"] == "SERVICE_LIMIT"


def test_check_email_statuses_and_limit(client, mails, monkeypatch):
    assert client.post(f"{BASE}/check-email", json={"email": EMAIL}).json() == {"status": "AVAILABLE"}
    sql(
        "INSERT INTO users (email, name, password_hash, team, approved_at) "
        "VALUES (:e, 'x', 'h', 'GURU', now())",
        e=EMAIL,
    )
    assert client.post(f"{BASE}/check-email", json={"email": EMAIL}).json() == {"status": "REGISTERED"}
    assert client.post(f"{BASE}/send-code", json={"email": EMAIL}).status_code == 409
    monkeypatch.setattr(settings, "ip_hourly_check_limit", 2)
    assert client.post(f"{BASE}/check-email", json={"email": EMAIL}).status_code == 429


def test_blocked_user_can_sign_up_again(client, mails):
    sql(
        "INSERT INTO users (email, name, password_hash, team, approved_at, blocked_at) "
        "VALUES (:e, 'x', 'h', 'GURU', now(), now())",
        e=EMAIL,
    )
    assert client.post(f"{BASE}/check-email", json={"email": EMAIL}).json() == {"status": "AVAILABLE"}
    token = verified_token(client, mails)
    assert client.post(BASE, json={**FORM, "signup_token": token}).status_code == 201
    assert sql("SELECT count(*) FROM users").scalar() == 2


def test_only_company_ip_allowed(client, mails, monkeypatch):
    monkeypatch.setattr(settings, "company_ips", "203.0.113.0/24")
    for path, body in (("check-email", {"email": EMAIL}), ("send-code", {"email": EMAIL})):
        r = client.post(f"{BASE}/{path}", json=body)
        assert r.status_code == 403 and r.json()["detail"]["code"] == "NOT_COMPANY_NETWORK"
    # 헤더를 위조해도 소용없다
    r = client.post(f"{BASE}/send-code", json={"email": EMAIL}, headers={"X-Forwarded-For": "203.0.113.5"})
    assert r.status_code == 403 and not mails


@pytest.mark.parametrize(
    "field,value",
    [
        ("password", "Short1!"),
        ("password", "alllowercase1"),
        ("password", "Has space1!x"),
        ("password", "A1!" + "x" * 62),
        ("phone", "02-123-4567"),
        ("birth_date", "2999-01-01"),
        ("name", "   "),
        ("team", "OTHER"),
    ],
)
def test_signup_validation(client, field, value):
    r = client.post(BASE, json={**FORM, "signup_token": "t", field: value})
    assert r.status_code == 422


def test_role_cannot_be_chosen(client, mails):
    token = verified_token(client, mails)
    r = client.post(BASE, json={**FORM, "signup_token": token, "role": "ADMIN"})
    assert r.status_code == 201
    assert sql("SELECT role FROM users").scalar() == "MEMBER"


def test_mail_retries_4xx_then_marks_failed(client, monkeypatch):
    calls = []

    def boom(to, subject, body):
        calls.append(1)
        raise smtplib.SMTPResponseException(421, b"try later")

    monkeypatch.setattr(mailer, "send_email", boom)
    monkeypatch.setattr(mailer.time, "sleep", lambda s: None)
    assert client.post(f"{BASE}/send-code", json={"email": EMAIL}).status_code == 200
    assert len(calls) == 4  # 처음 1회 + 재시도 3회
    assert sql("SELECT failed FROM email_send_log").scalar() is True


def test_mail_5xx_fails_without_retry(client, monkeypatch):
    calls = []

    def boom(to, subject, body):
        calls.append(1)
        raise smtplib.SMTPResponseException(550, b"daily limit")

    monkeypatch.setattr(mailer, "send_email", boom)
    client.post(f"{BASE}/send-code", json={"email": EMAIL})
    assert len(calls) == 1
    assert sql("SELECT failed FROM email_send_log").scalar() is True
