from fastapi import APIRouter, Depends

from app.api.dependencies import authenticated
from app.db.session import get_db
from app.schemas.auth import UserOut
from app.schemas.users import ProfileUpdate
from app.services.sessions import user_data

router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("/me", response_model=UserOut)
def me(identity=Depends(authenticated, scope="function")):
    return user_data(identity[0])


@router.patch("/me", response_model=UserOut)
def update(
    body: ProfileUpdate,
    identity=Depends(authenticated, scope="function"),
    db=Depends(get_db),
):
    user, _ = identity
    user.name = body.name
    db.commit()
    return user_data(user)
