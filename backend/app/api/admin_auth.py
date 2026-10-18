# 관리자 API 의 권한 확인. 모든 관리자 라우트는 이 의존성 하나만 쓴다

from app.core.exceptions import ApiError
from app.models.users import User


def current_admin() -> User:
    """로그인한 ADMIN 사용자를 돌려준다.

    로그인 기능(codex/login 브랜치)이 머지되기 전이라 아직 사용자를 알 수 없어 항상 거부한다.
    머지되면 아래처럼 바꾼다. 테스트는 app.dependency_overrides 로 이 함수를 대체한다.

        def current_admin(identity=Depends(authenticated, scope="function")) -> User:
            user, _ = identity
            if user.role != Role.ADMIN:
                raise ApiError(403, "ADMIN_REQUIRED", "관리자만 사용할 수 있습니다.")
            return user
    """
    raise ApiError(501, "AUTH_NOT_READY", "로그인 기능 연동 후 사용할 수 있습니다.")
