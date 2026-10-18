from fastapi import APIRouter, Depends, Request, Response

from app.api.dependencies import authenticated, client_ip, delete_cookie, set_cookie
from app.core.config import settings
from app.core.exceptions import ApiError
from app.db.session import get_db
from app.schemas.auth import ExpiryOut, LoginIn, SessionOut
from app.services import auth, clock, sessions

router = APIRouter(prefix="/api/auth", tags=["login"])


@router.post("/login", response_model=SessionOut)
def login(body: LoginIn, request: Request, response: Response, db=Depends(get_db)):
    token, data = auth.login(db, client_ip(request), body.email, body.password)
    set_cookie(response, token)
    return data


@router.get("/me", response_model=SessionOut)
def me(identity=Depends(authenticated, scope="function")):
    return sessions.payload(*identity)


@router.post("/activity", response_model=ExpiryOut)
def activity(identity=Depends(authenticated, scope="function"), db=Depends(get_db)):
    sessions.touch(identity[1])
    db.commit()
    return {
        "idle_expires_at": identity[1].idle_expires_at,
        "absolute_expires_at": identity[1].absolute_expires_at,
    }


@router.post("/logout", status_code=204)
def logout(request: Request, db=Depends(get_db)):
    try:
        _, session = sessions.current(db, request.cookies.get(settings.cookie_name, ""))
    except ApiError as exc:
        if exc.status_code not in (401, 403):
            raise
        db.rollback()
    else:
        sessions.check_csrf(session, request.headers.get("X-CSRF-Token", ""))
        session.revoked_at = clock.now()
        db.commit()
    response = Response(status_code=204)
    delete_cookie(response)
    return response
