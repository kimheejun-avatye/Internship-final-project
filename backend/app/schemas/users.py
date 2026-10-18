from pydantic import BaseModel, ConfigDict, Field, field_validator


class ProfileUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=50)

    @field_validator("name")
    @classmethod
    def nonempty(cls, v):
        if not v.strip():
            raise ValueError("이름을 입력해주세요.")
        return v.strip()
