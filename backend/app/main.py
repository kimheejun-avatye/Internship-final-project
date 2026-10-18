from fastapi import FastAPI

from app.api.routes import auth, login, password, rooms
from app.api.session_security import install_session_security
from app.core.config import settings

if not settings.secret_key:
    raise RuntimeError("Set SECRET_KEY in root .env")

app = FastAPI(title="Meeting Room API")
app.include_router(auth.router)
app.include_router(rooms.router)
app.include_router(login.router)
app.include_router(password.router)
install_session_security(app)


@app.get("/health")
def health():
    return {"status": "ok"}
