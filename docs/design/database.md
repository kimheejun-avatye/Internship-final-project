# ERD 기준과 모델 파일

사용자가 제공한 ERD의 네 테이블과 컬럼 구성을 그대로 기준으로 삼는다. 이 문서는 파일 위치를 정리하며 컬럼명·타입·NULL 조건·관계를 변경하지 않는다. 참조 채팅의 과거 일기 서비스 DB는 이번 프로젝트의 테이블 기준이 아니다.

| 테이블 | 모델 파일 | ERD 컬럼 |
|---|---|---|
| users | backend/app/models/users.py | user_id, email, password_hash, team, role, created_at, updated_at, blocked_at |
| refresh_token | backend/app/models/refresh_token.py | token_id, user_id, Refresh_token, created_at, expired_at, verified_at |
| rooms | backend/app/models/rooms.py | room_id, name, status, capacity |
| reservations | backend/app/models/reservations.py | reservation_id, room_id, user_id, name, title, start_at, end_at, created_at, participants |

- users → refresh_token: 1:N
- users → reservations: 1:N
- rooms → reservations: 1:N

사용자 정보는 users.py 한 곳에 정의한다. 인증 처리는 이 모델을 사용하며 별도 계정 테이블을 만들지 않는다. participants는 ERD의 INT 컬럼을 유지하고 별도 참석자 테이블을 만들지 않는다.

현재 모델 파일은 비어 있으며 실제 DB나 마이그레이션은 생성하지 않았다.
