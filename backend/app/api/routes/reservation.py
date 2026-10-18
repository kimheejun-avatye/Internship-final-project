"""예약·캘린더 컨트롤러 스켈레톤. 클래스 선언은 HTTP 경로를 등록하지 않는다."""

from typing import Any
from uuid import UUID

from app.models.users import User
from app.schemas.rooms import RoomOut
from app.services.reservations import ReservationService


# 예약·캘린더의 요청과 인증 사용자 정보를 받아 서비스에 전달하는 컨트롤러
class ReservationController:
    """인증된 User를 외부에서 받는다. 인증과 FastAPI DI 연결은 아직 없다."""

    # 생성자: 예약 조회 업무를 위임할 서비스 객체를 외부에서 주입받는다.
    def __init__(self, service: ReservationService) -> None:
        self.service = service

    # 캘린더 예약 조회: 조회 기간·필터와 인증 사용자 ID를 서비스에 전달한다.
    def get_calendar_reservations(self, query: Any, current_user: User) -> list[Any]:
        """제안: GET /calendar/reservations. 일·주·월 조회는 기간만 다르게 받는다.

        TODO: 없는 CalendarQuery 및 CalendarReservationResponse 정의 후 Any를
        각각 해당 DTO와 list[CalendarReservationResponse]로 교체한다.
        요청 계약: 시간대가 있는 start_at/end_at, scope(all/mine), 선택적 room_id.
        TODO: DTO에서 end_at > start_at 검증. 응답 계약은 서비스 주석 참조.
        TODO: 인증 의존성이 제공한 current_user.user_id와 query를
        service.get_calendar_reservations에 전달하고 DTO 리스트를 반환한다.
        컨트롤러에서는 쿼리·날짜·업무 조건을 계산하지 않는다.
        """
        raise NotImplementedError

    # 회의실 목록 조회
    def get_calendar_rooms(self, current_user: User) -> list[RoomOut]:
        """로그인 사용자에게 회의실 선택 항목을 제공하는 조회 메서드.

        캘린더에서 회의실별 예약을 필터링하거나 예약 페이지에서 회의실을
        선택할 때 사용할 목록을 서비스에 요청한다.
        입력: 인증 의존성이 제공할 current_user(User).
        반환: 회의실 ID·이름·상태·수용 인원을 담은 list[RoomOut].
        제안 경로: GET /calendar/rooms. 현재는 미등록·미구현 스켈레톤이다.

        TODO: 로그인 인증을 연결한 뒤 service.get_calendar_rooms를 호출한다.
        기존 RoomOut(room_id, name, status, capacity)을 재사용한다.
        인증 필요성을 명시하기 위해 current_user를 받으며, HTTP 연결은 하지 않는다.
        """
        raise NotImplementedError

    # 내 금일 예약 조회: 인증 사용자 ID·선택 회의실·페이지 번호를 서비스에 전달한다.
    def get_my_today_reservations(
        self, room_id: UUID, current_user: User, page: int = 1
    ) -> Any:
        """제안: GET /reservations/my/today. 내 금일 예약의 페이지 응답.

        요청 계약: room_id, page(1 이상). 응답 계약: items, total, page, page_size=5.
        TODO: 페이지 요청/응답 DTO가 정의되면 Any 응답 타입을 교체하고 검증 연결.
        TODO: 인증된 current_user.user_id, room_id, page만
        service.get_my_today_reservations에 전달한다.
        사용자 ID는 클라이언트 입력으로 받지 않는다. 날짜·scope·page_size도
        클라이언트 옵션으로 제공하지 않고 서비스가 결정한다.
        """
        raise NotImplementedError
