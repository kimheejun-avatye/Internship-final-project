from pydantic import BaseModel, Field, field_validator

from app.schemas.auth import SignupIn


class NewPassword(BaseModel):
    new_password: str = Field(max_length=128)

    @field_validator("new_password")
    @classmethod
    def valid_password(cls, value):
        return SignupIn._password(value)


class PasswordChangeIn(NewPassword):
    current_password: str = Field(min_length=1, max_length=128)


class PasswordResetIn(NewPassword):
    reset_token: str = Field(min_length=20, max_length=256)


class ResetSendOut(BaseModel):
    message: str
    cooldown_seconds: int
    expires_in: int


class ResetVerifyOut(BaseModel):
    reset_token: str
    expires_in: int
