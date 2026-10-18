from fastapi import FastAPI

from app.api.routes import auth, rooms
from app.core.config import settings

if not settings.secret_key:
    raise RuntimeError("Set SECRET_KEY in root .env")

app = FastAPI(title="Meeting Room API")
app.include_router(auth.router)
app.include_router(rooms.router)


@app.get("/health")
def health():
    return {"status": "ok"}
