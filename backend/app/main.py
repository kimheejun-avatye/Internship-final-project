import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes import auth, login, password, rooms, users
from app.core.config import settings
from app.core.exceptions import ApiError
from app.db.session import SessionLocal
from app.services import login_limits

if len(settings.secret_key) < 32:
    raise RuntimeError("SECRET_KEY must contain at least 32 characters")
if settings.production and not (settings.smtp_user and settings.smtp_password):
    raise RuntimeError("SMTP must be configured in production")

if settings.production and (
    not settings.origins
    or any(not origin.startswith("https://") for origin in settings.origins)
):
    raise RuntimeError("Production APP_ORIGINS must contain HTTPS origins")

app = FastAPI(title="Meeting Room API")
for router in (auth.router, login.router, password.router, users.router, rooms.router):
    app.include_router(router)


@app.middleware("http")
async def browser_guard(request: Request, call_next):
    if request.url.path.startswith("/api") and request.method not in (
        "GET",
        "HEAD",
        "OPTIONS",
    ):
        if request.headers.get("origin") not in settings.origins:
            return JSONResponse(
                {
                    "detail": {
                        "code": "CSRF_FAILED",
                        "message": "허용하지 않은 요청 출처입니다.",
                    }
                },
                status_code=403,
            )
        if (
            request.headers.get("content-type", "").split(";")[0].strip()
            != "application/json"
        ):
            return JSONResponse(
                {
                    "detail": {
                        "code": "CONTENT_TYPE",
                        "message": "JSON 요청이 필요합니다.",
                    }
                },
                status_code=415,
            )
    if request.url.path == "/api/auth/login" and request.method == "POST":
        try:
            with SessionLocal() as db:
                login_limits.ip_limit(
                    db, request.client.host if request.client else "unknown"
                )
        except ApiError as exc:
            return JSONResponse(
                {"detail": exc.detail}, status_code=exc.status_code, headers=exc.headers
            )
        except SQLAlchemyError:
            return JSONResponse(
                {
                    "detail": {
                        "code": "SERVICE_UNAVAILABLE",
                        "message": "일시적인 서버 오류입니다.",
                    }
                },
                status_code=503,
            )
    response = await call_next(request)
    response.headers["Cache-Control"] = "no-store"
    response.headers["X-Content-Type-Options"] = "nosniff"
    return response


@app.exception_handler(SQLAlchemyError)
async def database_error(request, exc):
    logging.getLogger(__name__).error("Database operation failed", exc_info=exc)
    return JSONResponse(
        {
            "detail": {
                "code": "SERVICE_UNAVAILABLE",
                "message": "일시적인 서버 오류입니다. 다시 시도해주세요.",
            }
        },
        status_code=503 if request.url.path.startswith("/api/") else 500,
    )


@app.get("/health")
def health():
    return {"status": "ok"}
