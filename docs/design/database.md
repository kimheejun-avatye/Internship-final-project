# PostgreSQL ERD

마이그레이션 `backend/migrations/versions/0001_initial_schema.py` (revision `0001`) 기준이다.
널 여부의 `불가`는 `NOT NULL`, `허용`은 `NULL`을 뜻한다.

## users

| 컬럼명 | 타입 | 널 여부 |
|---|---|---|
| user_id | UUID | 불가 |
| email | TEXT | 불가 |
| password_hash | TEXT | 불가 |
| team | user_team ENUM (AVATYE, GURU) | 불가 |
| role | user_role ENUM (ADMIN, MEMBER) | 불가 |
| created_at | TIMESTAMP WITHOUT TIME ZONE | 불가 |
| updated_at | TIMESTAMP WITHOUT TIME ZONE | 허용 |
| blocked_at | TIMESTAMPTZ | 허용 |

PK: `user_id`. UNIQUE: `email`.

## refresh_token

| 컬럼명 | 타입 | 널 여부 |
|---|---|---|
| token_id | UUID | 불가 |
| user_id | UUID | 불가 |
| Refresh_token | TEXT | 불가 |
| created_at | TIMESTAMPTZ | 불가 |
| expired_at | TIMESTAMPTZ | 허용 |
| verified_at | TIMESTAMPTZ | 불가 |

PK: `token_id`. FK: `user_id` → `users.user_id`.

`Refresh_token`은 원본의 대문자를 유지한다. 직접 SQL을 작성할 때는 `"Refresh_token"`처럼 큰따옴표로 감싼다.

## rooms

| 컬럼명 | 타입 | 널 여부 |
|---|---|---|
| room_id | UUID | 불가 |
| name | TEXT | 불가 |
| status | room_status ENUM (ACTIVE, BLOCK) | 불가 |
| capacity | INTEGER | 불가 |

PK: `room_id`.

## reservations

| 컬럼명 | 타입 | 널 여부 |
|---|---|---|
| reservation_id | UUID | 불가 |
| room_id | UUID | 불가 |
| user_id | UUID | 불가 |
| name | TEXT | 불가 |
| title | TEXT | 불가 |
| start_at | TIMESTAMPTZ | 불가 |
| end_at | TIMESTAMPTZ | 불가 |
| created_at | TIMESTAMPTZ | 불가 |
| participants | INTEGER | 허용 |

PK: `reservation_id`. FK: `room_id` → `rooms.room_id`, `user_id` → `users.user_id`.

## 관계 및 적용 기준

- users → refresh_token: 1:N
- users → reservations: 1:N
- rooms → reservations: 1:N

각 자식 행은 반드시 부모 한 행을 참조한다. FK는 PostgreSQL 기본 동작인 `NO ACTION`을 사용하며 연쇄 삭제하지 않는다.
원본 주석의 PK·FK·UNIQUE는 실제 제약으로 적용했다. 이름과 컬럼이 정의되지 않은 빈 `Untitled` 테이블은 제외했다.
UUID와 시간 컬럼에 자동 생성 기본값은 추가하지 않았으므로 INSERT 시 필수 값을 전달해야 한다.
`TIMESTAMPTZ`는 `TIMESTAMP WITH TIME ZONE`이다. `users.created_at`과 `users.updated_at`은 원본대로 시간대 없는 타입을 유지한다.

Alembic은 별도로 `alembic_version` 관리 테이블을 생성한다.

| 컬럼명 | 타입 | 널 여부 |
|---|---|---|
| version_num | VARCHAR(32) | 불가 |

PK: `version_num`. 이 테이블은 애플리케이션 도메인 테이블이 아니다.

## 마이그레이션 실행

Python 3.9 이상과 Docker Compose가 필요하다. 최초 실행에는 Python 패키지 다운로드를 위한 네트워크 접근이 필요하다.
프로젝트 루트에 `.env`가 없다면 `.env.example`을 복사하고 접속 정보를 설정한다.

```bash
cp .env.example .env  # 최초 설정 시에만 실행
```

```bash
docker compose up -d --wait
bash backend/scripts/migrate.sh
bash backend/scripts/migrate.sh current
```

스크립트는 `backend/.venv`를 생성하고 `backend/requirements-migrations.txt`의 의존성을 설치한다.
인수가 없으면 `upgrade head`를 실행한다. 이미 적용된 revision은 다시 실행하지 않는다.
접속 주소는 `127.0.0.1`이며, 루트 `.env`의 `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`를 사용한다.
터미널 환경변수는 `.env`보다 우선한다. DB 서버 자체와 데이터베이스는 Compose가 생성하고, 테이블은 Alembic이 생성한다.

추가 마이그레이션 파일을 만들 때:

```bash
bash backend/scripts/migrate.sh revision -m "describe schema change"
```

모델 파일은 아직 비어 있어 자동 생성 대신 새 revision의 `upgrade`와 `downgrade`를 직접 작성한다.

직전 revision으로 되돌릴 때:

```bash
bash backend/scripts/migrate.sh downgrade -1
```

초기 revision을 되돌리면 네 테이블과 ENUM 타입이 삭제되며 테이블 데이터도 삭제된다.
