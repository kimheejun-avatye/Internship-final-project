# 파일 구조와 책임

역할별 계층 구조를 사용한다. 같은 기능은 각 계층에서 같은 이름으로 찾는다. 예를 들어 예약은 `api/routes/reservations.py`, `schemas/reservations.py`, `services/reservations.py`, `models/reservations.py`로 연결된다.

| 영역 | 책임 |
|---|---|
| api/routes | HTTP 입력을 받고 서비스를 호출한 뒤 응답한다. |
| schemas | 요청·응답 데이터의 형식과 검증 조건을 정의한다. |
| services | 업무 규칙을 처리하고 DB 조회·저장을 수행한다. |
| models | 네 테이블의 컬럼·관계·제약을 정의한다. |
| core | 설정·보안 도구·공통 오류를 제공한다. |
| db | DB 연결과 세션, 모델 기반을 제공한다. |
| migrations | 실제 DB 스키마 변경 이력을 관리한다. |

`db/session.py`의 세션은 DB 작업 단위이며 로그인 기록 테이블을 뜻하지 않는다. `schemas/auth.py`와 `services/auth.py`도 별도 테이블을 뜻하지 않는다.

현재 단계에서는 빈 구현 파일만 배치한다. 인증 정책과 업무 규칙은 개발 단계에서 확정한다. 이메일 인증·별도 로그인 기록·예약 참석자 연결 테이블을 추가하는 구조로 확장하지 않는다.

프런트엔드와 백엔드는 분리한다. 화면은 API를 호출하고 FastAPI가 PostgreSQL에 접근한다.
