from typing import Literal, Optional
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, model_validator


# 캘린더 예약 조회 요청: 일·주·월 조회에서 공통으로 사용하는 기간과 필터
class CalendarQuery(BaseModel):
    """시작 포함·종료 제외 구간과 겹치는 예약을 조회하기 위한 요청 DTO."""

    start_at: AwareDatetime
    end_at: AwareDatetime
    scope: Literal["all", "mine"] = "all"
    room_id: Optional[UUID] = None

    # 조회 기간 검증: 종료 시각은 시작 시각보다 늦어야 한다.
    @model_validator(mode="after")
    def validate_period(self) -> "CalendarQuery":
        if self.end_at <= self.start_at:
            raise ValueError("조회 종료 시각은 시작 시각보다 늦어야 합니다.")
        return self
