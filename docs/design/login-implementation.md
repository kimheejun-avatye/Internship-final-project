# 로그인 구현과 실행 안내

작성일: 2026년 10월 18일. 작업 루트는 `/Users/kimheejun/teamproject1`이다.

## 구현 범위

서버 세션 로그인, 현재 회원 조회, 현재 세션 로그아웃, 사용자 활동 연장, 내 프로필 이름 수정, 현재 비밀번호로 비밀번호 변경, 이메일 코드 기반 비밀번호 재설정을 구현했다. 회원가입은 `feat/sign-up` 코드를 통합했다. 로그인·회원가입 프론트는 기존 팀원 코드를 기반으로 한다.

로그인과 회원가입은 `AuthLayout`, 내 프로필은 `ProtectedRoute → AppLayout`에 배치했다. `AuthProvider`는 서버 `/api/auth/me`로 로그인 상태를 복원한다. 실제 권한·차단·승인·만료 검사는 서버가 수행한다.

## 실행

Python 3.10 이상, uv, Docker Compose, Node `^22.22.2 || ^24.15.0 || >=26.0.0`가 필요하다.

루트 `.env`에는 기존 PostgreSQL 설정 외에 `SECRET_KEY`를 32자 이상 무작위 값으로 설정한다. 값을 만들려면 `python3 -c 'import secrets; print(secrets.token_urlsafe(48))'`를 사용한다. 생성값은 서버 `.env`에만 보관한다. 브라우저 코드나 Git에 올리지 않는다. `.env.example`을 참고한다.

프로젝트 루트에서:

```bash
docker compose up -d postgres
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload --host 127.0.0.1 --port 8001 --no-proxy-headers
```

별도 터미널에서:

```bash
cd /Users/kimheejun/teamproject1/frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5174
```

기본 프록시는 8000번이다. 위처럼 8001번을 사용할 경우 `frontend/.env.local`에 `BACKEND_URL=http://127.0.0.1:8001`을 설정한다. 개발 서버를 재시작하거나 설정 재로딩을 확인한다. 브라우저는 `http://127.0.0.1:5174/login`, API 문서는 `http://127.0.0.1:8001/docs`에서 확인한다. 프론트와 API의 호스트는 `localhost` 또는 `127.0.0.1` 중 하나로 통일한다.

회원가입 완료 계정은 기존 정책에 따라 승인 대기 상태이다. 운영 권한이 있는 담당자가 백엔드 폴더에서 다음 명령으로 기존 계정을 승인한 후 로그인한다. 차단 계정은 이 명령으로 승인할 수 없다.

```bash
uv run python -m app.admin member@example.com
```

개발 중 SMTP 설정이 없으면 인증 메일은 백엔드 터미널 로그에 출력된다. 운영에서는 `APP_ENV=production`, SMTP 계정·비밀번호, 실제 HTTPS `APP_ORIGINS`를 설정해야 한다. 운영에서 콘솔 코드 발송 모드는 허용하지 않는다.

## 세션 정책

- 쿠키: 로컬 `session`, 운영 `__Host-session`. HttpOnly, SameSite=Lax, Path=/, 운영 Secure. 쿠키 유효 시간은 8시간이며 실제 비활동 만료는 서버에서 검사한다.
- 세션 원문은 브라우저 쿠키에, SHA-256 해시는 DB `user_sessions.token_hash`에 저장한다. JWT·리프레시 토큰·localStorage 기반 인증은 사용하지 않는다.
- 비활동 30분, 절대 만료 8시간. 절대 만료를 넘겨 연장하지 않는다.
- `/me`·자동 조회는 연장하지 않는다. 실제 사용자 입력·클릭이 있으면 프론트가 최대 60초에 한 번 `/activity`를 보낸다. 명시적인 사용자 API 요청은 `X-Session-Activity: user`로 표시한다.
- 여러 기기는 별도 세션, 같은 브라우저 탭은 쿠키 공유. 일반 로그아웃은 현재 세션만, 비밀번호 변경·재설정은 모든 세션을 폐기한다.
- 변경 요청은 Origin·JSON Content-Type을 검사한다. 세션이 있는 변경 요청에는 세션에 연결한 `X-CSRF-Token`도 필요하다.

## API와 파일 위치

- `backend/app/api/routes/auth.py`: 팀원 회원가입 API, 기존 URL 유지.
- `backend/app/api/routes/login.py`: POST `/api/auth/login`, GET `/api/auth/me`, POST `/api/auth/logout`, POST `/api/auth/activity`.
- `backend/app/api/routes/password.py`: POST `/api/auth/password/change`, `/reset/send-code`, `/reset/verify-code`, `/reset`.
- `backend/app/api/routes/users.py`: GET·PATCH `/api/users/me`. 사용자 수정 필드는 이름만 허용한다.
- `backend/app/api/dependencies.py`: 세션·CSRF 검증, 요청 완료 후 활동 갱신과 잠금 해제.
- `backend/app/services/{auth,sessions,login_limits,passwords}.py`: 업무 규칙과 트랜잭션.
- `backend/app/core/security.py`: Argon2id 공통 함수. 기존 RFC 9106의 64MiB·3회·병렬 4 설정 재사용.
- `backend/migrations/versions/0003_login_sessions.py`: 세션·제한·재설정 테이블과 이메일 전체 고유 인덱스.
- `frontend/src/auth/`: 인증 상태와 보호 라우트.
- `frontend/src/layouts/`: 인증 화면·앱 공통 틀.
- `frontend/src/shared/api/`: 쿠키·CSRF를 포함한 공통 요청 및 기능 API.

성공 응답에는 사용자 정보와 만료 시각을 반환하며 비밀번호 해시·세션 원문을 JSON에 포함하지 않는다. 오류는 `{"detail":{"code":"...","message":"..."}}`, 제한 오류는 `retry_after`와 `Retry-After` 헤더를 포함한다. 입력 오류는 FastAPI의 422 필드 오류를 프론트에서 해석한다.

## 요청 제한과 동시성

로그인 이메일은 trim·lower로 정규화한다. 최근 15분의 비밀번호 실패 5회에서 5분 잠금을 설정하고, 잠금 중 요청은 시간을 늘리지 않는다. 잠금 해제 후에는 새 실패 구간을 시작한다. 성공 시 이메일 실패 기록을 지운다. 계정이 없는 경우도 더미 해시로 검증한다. DB·서버 오류는 비밀번호 실패로 기록하지 않는다. 로그인 IP 제한은 유효하지 않은 입력을 포함해 1분 30회이며 허용된 출처의 JSON 요청에 적용한다.

현재 비밀번호 변경 시 추측 공격에도 별도 실패 제한과 IP 제한을 적용한다. 재설정은 발송·코드 확인·완료 각각 IP 제한이 있으며 코드 실패 5회에 잠근다. 인증번호 발송은 기존 시간당 이메일 5회·IP·서비스 한도를 공유하고, 서버 발송 실패는 사용자 발송 횟수에 포함하지 않는다. 가입 인증과 비밀번호 재설정 인증은 분리해 용도 혼용을 막았다.

회원 행 → 세션 행의 잠금 순서를 공유해 로그인과 비밀번호 변경의 경쟁을 처리한다. 가입 회원 생성과 인증 소비, 비밀번호 변경·재설정과 전체 세션 폐기는 각각 같은 트랜잭션이다. 이메일 UNIQUE 위반만 409 `EMAIL_ALREADY_EXISTS`로 변환한다.

`0003`은 차단된 계정까지 포함한 전체 이메일 고유 제약을 추가한다. 기존 DB에 같은 이메일이 이미 여러 개 있으면 마이그레이션이 실패하며 데이터를 자동 삭제하지 않는다. 이 경우 계정 정리 정책을 정한 후 진행한다. 기존 `refresh_token` 테이블은 삭제하지 않고 사용만 중단한다.

## 테스트

테스트는 이름이 `_test`로 끝나는 **별도 PostgreSQL DB**만 허용하며 각 테스트 시작 시 해당 DB의 인증·회원 데이터를 비운다. 실제 개발 DB 주소를 넘기지 않는다.

```bash
cd backend
TEST_DATABASE_URL=postgresql+psycopg://USER:PASSWORD@127.0.0.1:PORT/meeting_room_test uv run pytest -q
uv run ruff check app tests
```

```bash
cd frontend
npm test
npm run build
```

로그인 성공·실패·잠금 경계·IP 제한, 승인·차단, 세션 만료, 다중 세션·로그아웃, CSRF, 프로필 필드 제한, 코드·토큰 만료·일회용, DB 실패 롤백, 동시 요청을 검증한다. 기존 회원가입의 이메일 인증·발송 제한 테스트도 포함한다.

## 운영 시 연결할 항목

실제 SMTP 자격 증명, 관리자 승인 운영 화면, HTTPS 프록시와 실제 Origin 설정은 배포 환경에서 연결한다. 신뢰하는 프록시가 있을 때만 프록시 헤더 처리를 켠다. `python -m app.maintenance`는 30일이 지난 만료 세션·요청 기록·재설정 기록을 정리한다. 스케줄 실행은 운영 담당자가 설정하며 이번 작업에서 자동화는 생성하지 않았다. 예약·달력·관리자 화면은 이번 구현에 포함하지 않는다.

## 이번 구현 검증 결과

- 실제 작업 폴더에서 PostgreSQL 기반 백엔드 테스트 57개 통과.
- 로그인·회원가입 프론트 테스트 19개 통과. TypeScript 검사와 프로덕션 빌드 성공.
- 기존 데이터 보존, 중복 이메일에서의 마이그레이션 중단·롤백, 0002→0003→0002→0003 왕복 확인.
- 브라우저에서 잘못된 로그인 거절과 비밀번호 찾기 화면 이동 확인.
- 로컬 PostgreSQL과 백엔드 8001, 프론트 5174 연결 확인. 실제 SMTP 전달은 자격 증명이 없어 검증하지 않음.
- Git 커밋·원격 푸시는 수행하지 않았음.
