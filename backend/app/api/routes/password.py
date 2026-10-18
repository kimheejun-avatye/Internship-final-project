from fastapi import APIRouter, Depends, Request, Response

from app.api.dependencies import client_ip, delete_cookie, password_authenticated
from app.db.session import get_db
from app.schemas.auth import EmailIn, VerifyCodeIn
from app.schemas.password import (
    PasswordChangeIn,
    PasswordResetIn,
    ResetSendOut,
    ResetVerifyOut,
)
from app.services import passwords

router = APIRouter(prefix="/api/auth/password", tags=["password"])


@router.post("/change", status_code=204)
def change(
    body: PasswordChangeIn,
    request: Request,
    identity=Depends(password_authenticated, scope="function"),
    db=Depends(get_db),
):
    # Dependency holds member/session locks. Keep one lock order; quota takes its own transaction first elsewhere.
    user, _ = identity
    passwords.change(db, user, body.current_password, body.new_password)
    response = Response(status_code=204)
    delete_cookie(response)
    return response


@router.post("/reset/send-code", response_model=ResetSendOut)
def send_code(body: EmailIn, request: Request, db=Depends(get_db)):
    return passwords.send_code(db, client_ip(request), body.email)


@router.post("/reset/verify-code", response_model=ResetVerifyOut)
def verify_code(body: VerifyCodeIn, request: Request, db=Depends(get_db)):
    return passwords.verify_code(db, client_ip(request), body.email, body.code)


@router.post("/reset", status_code=204)
def reset(body: PasswordResetIn, request: Request, db=Depends(get_db)):
    passwords.reset(db, client_ip(request), body.reset_token, body.new_password)
    response = Response(status_code=204)
    delete_cookie(response)
    return response
