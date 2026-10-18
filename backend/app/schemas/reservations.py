import uuid
from datetime import datetime
from typing import Literal, Optional
from uuid import UUID

from pydantic import AwareDatetime, BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.users import Team


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


# 캘린더 예약 조회 응답: 날짜·주간·월간 목록에서 공통으로 반환하는 예약 한 건
class CalendarReservationResponse(BaseModel):
    """목록 API는 페이지 정보 없이 list[CalendarReservationResponse]를 반환한다.

    회의실 이름과 참석 정보는 서비스에서 조회·계산해 구성한다.
    Reservation ORM을 그대로 직렬화하는 DTO가 아니다.
    """

    reservation_id: UUID
    title: str
    room_id: UUID
    room_name: str
    organizer_id: UUID = Field(description="예약 생성자: Reservation.user_id")
    start_at: AwareDatetime
    end_at: AwareDatetime
    participant_count: int = Field(
        ge=0, description="reservation_attendees 기준 참석 인원수"
    )
    is_mine: bool = Field(description="예약 생성자가 로그인 사용자와 같은지 여부")
    is_attending: bool = Field(
        description="로그인 사용자가 reservation_attendees에 등록되어 있는지 여부"
    )


# 컨트롤러가 서비스에 전달할 조회 조건 데이터
class ReservationListQuery(BaseModel):
    room_id: uuid.UUID
    page: int = Field(default=1, ge=1)

# 예약 한 건의 응답
class ReservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    reservation_id: uuid.UUID
    room_id: uuid.UUID
    user_id: uuid.UUID
    title: str
    start_at: datetime
    end_at: datetime
    participant_count: int = Field(ge=0)
    team: Team

# 예약 목록과 페이지 정보
class ReservationListOut(BaseModel):
    items: list[ReservationOut]
    total: int = Field(ge=0)
    page: int = Field(ge=1)
    page_size: int = 5


class ReservationCreateIn(BaseModel):
    """예약자 ID는 입력으로 받지 않고 컨트롤러에서 전달한다."""

    model_config = ConfigDict(extra="forbid")

    room_id: UUID
    title: str
    start_at: AwareDatetime
    end_at: AwareDatetime

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        title = value.strip()
        if not title:
            raise ValueError("회의 제목을 입력해 주세요.")
        return title

    @model_validator(mode="after")
    def validate_period(self) -> "ReservationCreateIn":
        if self.end_at <= self.start_at:
            raise ValueError("종료 시각은 시작 시각보다 늦어야 합니다.")
        return self


class ReservationCreateOut(BaseModel):
    """저장이 확정된 예약 한 건의 정보."""

    model_config = ConfigDict(from_attributes=True)

    reservation_id: UUID
    room_id: UUID
    user_id: UUID
    title: str
    start_at: AwareDatetime
    end_at: AwareDatetime
    created_at: AwareDatetime
