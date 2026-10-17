from typing import Literal, Self
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, model_validator

# 클라이언트가 예약 목록을 조회 할 때 보내는 조건을 정의한다
class CalendarQuery(BaseModel):
    # 포함
    start_at: AwareDatetime

    # 제외
    end_at: AwareDatetime

    # all: 전체 예약 / mine: 내가 생성한 예약
    scope: Literal["all", "mine"] = "all"

    # 생략하면 전체 회의실 조회
    room_id: UUID | None = None

    # 조회 기간이 올바른지 검사
    @model_validator(mode="after")
    def validate_period(self) -> Self:
        if self.end_at <= self.start_at:
            raise ValueError("end_at은 start_at보다 늦어야 합니다.")
        return self