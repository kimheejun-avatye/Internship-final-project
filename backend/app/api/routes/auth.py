from fastapi import APIRouter, BackgroundTasks, Depends, Request
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.schemas.auth import (
    CheckEmailOut,
    EmailIn,
    SendCodeOut,
    SignupIn,
    SignupOut,
    VerifyCodeIn,
    VerifyCodeOut,
)
from app.services import mailer, signup

router = APIRouter(prefix="/api/auth/signup", tags=["signup"])


def client_ip(request: Request) -> str:
    # 서버가 직접 받은 연결의 IP 만 쓴다. X-Forwarded-For 는 위조할 수 있어 읽지 않는다
    return request.client.host if request.client else ""


@router.post("/check-email", response_model=CheckEmailOut)
def check_email(body: EmailIn, request: Request, db: Session = Depends(get_db)):
    return {"status": signup.check_email(db, client_ip(request), body.email)}


@router.post("/send-code", response_model=SendCodeOut)
def send_code(
    body: EmailIn,
    request: Request,
    background: BackgroundTasks,
    db: Session = Depends(get_db),
):
    log_id, code = signup.send_code(db, client_ip(request), body.email)
    background.add_task(mailer.deliver_code, log_id, body.email, code)
    return {
        "cooldown_seconds": settings.resend_cooldown_seconds,
        "expires_in": settings.code_ttl_seconds,
    }


@router.post("/verify-code", response_model=VerifyCodeOut)
def verify_code(body: VerifyCodeIn, request: Request, db: Session = Depends(get_db)):
    token = signup.verify_code(db, client_ip(request), body.email, body.code)
    return {"signup_token": token, "expires_in": settings.signup_token_ttl_seconds}


@router.post("", response_model=SignupOut, status_code=201)
def create_account(body: SignupIn, request: Request, db: Session = Depends(get_db)):
    user = signup.signup(db, client_ip(request), body)
    return {"user_id": str(user.user_id), "status": "PENDING"}
