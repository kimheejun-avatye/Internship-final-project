# 로그인과 회원가입 연동 개발 계획서

작성일: 2026년 10월 18일
대상 저장소: /Users/kimheejun/teamproject1
작업 브랜치: codex/login
문서 상태: 구현 기준 설계. 구현 결과와 실행 방법은 [로그인 구현 안내](login-implementation.md)를 참고한다. 아래 현재 상태 항목은 구현 전 조사 기록이다.

## 1 목적과 현재 상태

회원가입 담당자의 코드를 재사용하면서 로그인, 세션 조회, 현재 세션 로그아웃, 내 프로필의 비밀번호 변경과 이메일 기반 재설정을 구현한다. 파일별 책임, 프론트 레이아웃, API와 DB 연결, CRUD 및 완료 조건을 정한다. 예약·달력·관리자 기능 자체는 이번 구현 범위가 아니다.

현장 확인 결과 현재 codex/login의 HEAD는 5ed8191이며 백엔드에는 health API만 실행 코드로 존재한다. 원격 feat/sign-up에는 회원가입 API·서비스·모델·메일러 및 0002_signup 마이그레이션이 있다. 로그인·회원가입 프론트는 feat/frontend-signup-api에서 선택적으로 가져온 미커밋 파일이다. 로그인 버튼은 API 없이 /reservations로 이동하는 임시 구현이며 현재 라우팅에는 예약 화면이 없다.

먼저 가져온 프론트 변경을 보존하고 feat/sign-up과의 차이를 검토해 회원가입 백엔드를 통합해야 한다. 문서 작성 단계에서 브랜치 병합이나 기능 코드는 변경하지 않는다. 개발 시작 시 상태를 다시 확인한다.

## 2 확정 정책

| 항목 | 내용 |
| --- | --- |
| 인증 | 서버 세션, 브라우저 쿠키로 세션 ID 전달 |
| 비활동 만료 | 마지막 인정 활동부터 30분 |
| 절대 만료 | 로그인 시각부터 8시간. 어떤 활동도 연장하지 못함 |
| 활동 인정 | 실제 사용자 동작에서 시작한 유효한 인증 요청 |
| 활동 제외 | 주기적 자동 조회, 앱 초기 세션 확인, 실패한 요청 |
| 다중 로그인 | 기기별 별도 세션 허용. 같은 브라우저의 탭은 쿠키 공유 |
| 로그아웃 | 현재 세션만 종료 |
| 비밀번호 변경 | 내 프로필에서 세션과 현재 비밀번호 확인, 새 비밀번호 설정 후 모든 세션 종료 |
| 비밀번호 재설정 | 로그인 화면에서 이메일 인증 후 새 비밀번호 설정, 모든 세션 종료 |
| 로그인 제한 | 정규화 이메일별 최근 15분간 검증 실패 5회면 5분 잠금. 잠금 중 연장 없음 |
| 성공·서버 오류 | 성공하면 이메일 실패 기록 초기화. 서버·DB 오류는 실패로 집계하지 않음 |
| IP 제한 | 같은 IP의 로그인 요청을 최근 1분간 30회 허용, 31번째 거절 |
| 가입 | 이메일 인증 후 회원 생성. 회원 생성과 인증 소비는 같은 트랜잭션 |
| 이메일 중복 | 정규화 이메일에 전체 UNIQUE. 충돌은 409 EMAIL_ALREADY_EXISTS |

인증번호 발송 최대 5회와 서버 발송 실패 제외는 유지한다. 5회의 집계 기간은 상단 정책에서 구체적으로 확정되지 않았으므로 기존 팀 설정을 확인한 뒤 결정한다. 인증번호 TTL은 합의된 3~5분 범위에서 기존 값을 확인한다.

## 3 브라우저에 무엇을 저장하는가

브라우저의 쿠키 저장소와 프론트 소스 파일은 서로 다르다. 세션 ID를 .tsx, .ts, .env 같은 프론트 파일에 적어두지 않는다.

| 위치 | 보관 내용 |
| --- | --- |
| 브라우저 HttpOnly 쿠키 | 추측 불가능한 임의의 세션 토큰 |
| 프론트 메모리 | 화면에 표시할 사용자 정보, CSRF 토큰, 초기 확인 상태 |
| 서버 DB | 세션 토큰의 해시, 회원 ID, 생성·활동·만료·폐기 시각 |
| 서버 환경변수 | 서버 비밀키, DB 주소, 쿠키·Origin 설정 |

세션 토큰은 secrets.token_urlsafe(32) 수준의 난수로 생성한다. 원문은 쿠키에만 전달하고 DB에는 SHA-256 해시를 저장하는 안이다. UUID 회원 ID와 세션 토큰은 별개다. localStorage와 sessionStorage에는 세션 토큰을 저장하지 않는다. 이번 인증 구조에는 JWT와 리프레시 토큰이 필요하지 않다.

운영 쿠키 제안: __Host-session, HttpOnly, Secure, SameSite=Lax, Path=/, Domain 생략, Max-Age 8시간. 로컬 HTTP에서는 session 이름과 Secure=False를 사용한다. 서버의 30분·8시간 검사가 최종 기준이며 쿠키가 남아 있어도 만료된 세션은 거절한다. 브라우저를 닫으면 반드시 종료되는 정책은 아니며, 현재의 8시간 쿠키 정책에 따른다.

## 4 전체 연결 구조

```text
브라우저 main.tsx
  → App.tsx 라우터
  → AuthProvider: 앱 시작 시 GET /api/auth/me
  → AuthLayout 또는 ProtectedRoute → AppLayout
  → 각 페이지의 폼
  → shared/api/auth.ts 또는 signup.ts
  → shared/api/client.ts: 쿠키 전송·CSRF 헤더·오류 해석
  → 개발 Vite /api 프록시 또는 운영 동일 Origin 프록시
  → FastAPI main.py: 라우터·예외 처리 등록
  → api/routes: 입력 DTO 검사·응답·쿠키 처리
  → services: 로그인·잠금·세션·비밀번호 업무 규칙
  → models + db/session.py
  → PostgreSQL
```

프론트는 DB에 직접 접속하지 않는다. 프론트 경로 /login과 서버 API /api/auth/login은 별개다. 개발 시 /api 요청은 Vite가 8000번 백엔드로 전달한다. 운영도 웹과 API를 동일 Origin으로 제공하는 안으로 시작한다.

## 5 백엔드 파일 배치와 책임

아래 경로는 모두 /Users/kimheejun/teamproject1/backend 기준이다. '신규'는 생성 계획이며 아직 구현된 파일이라는 뜻이 아니다.

| 파일 | 상태·담당 코드 |
| --- | --- |
| app/main.py | 기존. 회원가입·로그인·프로필 라우터, 공통 예외 처리 연결 |
| app/api/routes/auth.py | 팀원 회원가입 라우터 보존. 기존 prefix /api/auth/signup 유지 |
| app/api/routes/login.py | 신규. /api/auth의 login, me, logout, activity 및 CSRF 응답 처리 |
| app/api/routes/password.py | 신규. 비밀번호 변경과 재설정 API |
| app/api/routes/users.py | 기존 자리. /api/users/me 조회·수정. 로그인 서비스와 역할 구분 |
| app/api/dependencies.py | 신규. 세션 쿠키로 현재 사용자 확인, 상태·만료 검사, CSRF 의존성 |
| app/schemas/auth.py | 팀원 가입 DTO 보존. LoginIn, LoginOut, MeOut 등 추가 |
| app/schemas/password.py | 신규. 변경·재설정 입력 및 응답 DTO |
| app/schemas/users.py | 프로필 조회·수정 허용 필드. role·승인·차단 필드는 사용자 수정 불가 |
| app/services/signup.py | 팀원 코드 재사용. 가입·인증 및 이메일 고유 제약 처리 보완 |
| app/services/auth.py | 로그인 흐름: 제한 확인, 회원 조회, 해시 검증, 상태 확인, 세션 생성 |
| app/services/sessions.py | 신규. 세션 생성·검증·활동 갱신·현재/전체 폐기 |
| app/services/login_limits.py | 신규. 이메일 실패 기록·5분 잠금·IP 1분 제한 |
| app/services/passwords.py | 신규. 변경·재설정 및 모든 세션 폐기를 같은 트랜잭션으로 처리 |
| app/services/mailer.py | 팀원 메일러 재사용. 인증 목적별 제목·발송 처리 |
| app/core/security.py | 팀원 Argon2id hash_password·verify_password 재사용. 세션 난수·해시·CSRF 도구 추가 |
| app/core/config.py | 세션 1800/28800초, 쿠키 이름·보안 설정, Origin, 요청 제한 등 |
| app/core/exceptions.py | 공통 ApiError 및 JSON 형식 변환. 예상 밖 오류는 500으로 처리 |
| app/models/users.py | 팀원 User 재사용. 회원 상태·비밀번호·정규화 이메일 |
| app/models/user_sessions.py | 신규. DB 세션 모델 |
| app/models/login_attempts.py | 신규. 이메일별 실패 이벤트와 잠금 상태, IP 요청 이벤트 |
| app/models/password_reset_verifications.py | 신규 제안. 가입 인증과 분리된 재설정 인증 상태 |
| app/models/__init__.py | 신규 모델 등록. Alembic에서 모든 모델을 인식하도록 연결 |
| app/db/session.py | get_db 제공. 세션 수명 관리·예외 롤백. commit 주체는 서비스로 통일 |
| migrations/versions/<다음번호>_login_sessions.py | 신규. 현재 최신 revision 확인 후 세션·제한·재설정 스키마 추가 |
| app/services/refresh.py, app/models/refresh_token.py | 세션 방식에서는 사용하지 않음. 기존 DB 테이블 삭제는 별도 합의 후 수행 |

요청에 따른 쿠키 설정은 라우터가, 세션 상태 변경은 서비스가 맡는다. 서비스가 HTTP Response 객체에 의존하지 않게 한다. 별도 repository 계층은 이번 규모에서 추가하지 않고 서비스가 SQLAlchemy를 사용한다.

## 6 프론트 레이아웃과 파일 배치

경로 기준: /Users/kimheejun/teamproject1/frontend.

로그인·회원가입도 레이아웃 안에 둔다. 다만 로그인 후 내비게이션이 있는 AppLayout과 구분해 AuthLayout을 사용한다.

```text
main.tsx
└─ BrowserRouter
   └─ AuthProvider
      └─ App.tsx
         ├─ AuthLayout: 인증 화면 공통 배경·중앙 배치·Outlet
         │  ├─ /login → LoginPage
         │  ├─ /signup → SignupPage
         │  └─ /password/reset → PasswordResetPage
         └─ ProtectedRoute: 확인 중/미로그인/로그인 상태 분기
            └─ AppLayout: 헤더·로그아웃·메뉴·Outlet
               └─ /profile → ProfilePage → PasswordChangeForm
```

예약·달력 화면은 담당자가 구현한 후 AppLayout 아래에 연결한다. 로그인 성공 후 목적지는 원래 접근한 안전한 내부 경로, 없으면 /profile로 제안한다. 임시로 존재하지 않는 /reservations에 보내지 않는다. 로그인한 사용자의 인증 화면 접근은 앱 내부로 이동시키는 안이다.

| 파일 | 역할 |
| --- | --- |
| src/main.tsx | React 시작, BrowserRouter와 AuthProvider 연결 |
| src/App.tsx | 레이아웃별 중첩 Route 선언 |
| src/layouts/AuthLayout.tsx | 신규. 인증 화면 공통 틀. 각 페이지는 폼 내용 담당 |
| src/layouts/AppLayout.tsx | 신규 제안. 로그인 후 공통 틀. 팀원 기존 레이아웃과 중복 구현하지 않도록 확인 |
| src/auth/AuthProvider.tsx | 신규. user, loading, csrfToken, login, logout, reloadMe 관리 |
| src/auth/ProtectedRoute.tsx | 신규. 초기 확인 완료까지 대기, 미로그인 시 /login 이동 |
| src/pages/auth/LoginPage.tsx | 이메일·비밀번호, 전송 중 중복 클릭 방지, 401/403/429 안내 |
| src/pages/auth/SignupPage.tsx | 기존 팀원 화면·API 유지. AuthLayout으로 감싸며 중복 배경 제거 |
| src/pages/auth/PasswordResetPage.tsx | 신규. 이메일→코드→새 비밀번호 단계 |
| src/pages/profile/ProfilePage.tsx | 신규. 본인 정보 조회와 변경 폼 |
| src/pages/profile/PasswordChangeForm.tsx | 신규. 현재·새 비밀번호와 확인 입력 |
| src/shared/api/auth.ts | 신규. login, getMe, logout, activity 호출 |
| src/shared/api/password.ts | 신규. 변경·재설정 호출 |
| src/shared/api/signup.ts | 기존. 팀원 가입 경로 유지 |
| src/shared/api/client.ts | GET/POST/PATCH 공통 요청, credentials, CSRF 헤더, 오류·401 처리 |
| src/shared/hooks/useSessionActivity.ts | 신규. 실제 사용자 동작 추적, 활동 통지 절제. 폴링은 제외 |
| src/shared/types/auth.ts | 신규. User, LoginResponse, ApiError 타입 |
| src/styles/auth.css | 로그인·가입·재설정 공통 스타일 |
| src/styles/layout.css | 앱 레이아웃 스타일. 인증 폼 스타일과 분리 |

React의 ProtectedRoute는 화면 접근 편의를 위한 장치다. 실제 권한 검증은 각 백엔드 API에서 반드시 수행한다. 비밀번호 확인값은 화면에서 비교하고 서버에는 현재 비밀번호와 새 비밀번호만 보내는 안이다. 서버도 새 비밀번호 정책을 검증한다.

## 7 API 계약 제안

회원가입의 기존 URL을 유지한다. 오류 형식도 기존 client.ts와 맞춰 detail 내부 객체로 통일한다.

| 메서드·URL | 입력 | 성공 결과 |
| --- | --- | --- |
| POST /api/auth/signup/check-email | email | 200 status: AVAILABLE/REGISTERED/PENDING |
| POST /api/auth/signup/send-code | email | 200 cooldown_seconds, expires_in |
| POST /api/auth/signup/verify-code | email, code | 200 signup_token, expires_in |
| POST /api/auth/signup | 기존 SignupPayload | 201 user_id, status |
| POST /api/auth/login | email, password | 200 user, csrf_token, idle_expires_at, absolute_expires_at + Set-Cookie |
| GET /api/auth/me | 세션 쿠키 | 200 로그인과 같은 사용자·만료 정보 및 csrf_token |
| POST /api/auth/logout | 세션 쿠키, CSRF 헤더 | 204 본문 없음 + 쿠키 삭제 |
| POST /api/auth/activity | 세션 쿠키, CSRF 헤더 | 200 idle_expires_at, absolute_expires_at |
| GET /api/users/me | 세션 쿠키 | 200 본인 프로필 |
| PATCH /api/users/me | 허용된 프로필 변경값, 세션·CSRF | 200 갱신 프로필 |
| POST /api/auth/password/change | current_password, new_password, 세션·CSRF | 204 + 쿠키 삭제 |
| POST /api/auth/password/reset/send-code | email | 200 일반 안내, cooldown_seconds |
| POST /api/auth/password/reset/verify-code | email, code | 200 reset_token, expires_in |
| POST /api/auth/password/reset | reset_token, new_password | 204 |

User 응답 예: user_id, email, name, team, role. password_hash·세션 원문·DB 내부 잠금 정보는 반환하지 않는다. reset_token은 가입용 signup_token과 용도가 다르며 혼용을 금지한다. 재설정 발송은 회원 존재 여부에 관계없이 동일한 일반 안내를 반환하는 안이다.

오류 예:

```json
{"detail":{"code":"LOGIN_RATE_LIMITED","message":"잠시 후 다시 로그인해주세요.","retry_after":300}}
```

| 상태 | 코드 | 의미 |
| --- | --- | --- |
| 401 | INVALID_CREDENTIALS | 이메일 또는 비밀번호 불일치. 회원 유무를 구분하지 않음 |
| 401 | SESSION_REQUIRED / SESSION_EXPIRED / SESSION_REVOKED | 로그인 필요·세션 만료·폐기 |
| 403 | USER_PENDING / USER_BLOCKED | 올바른 비밀번호 확인 후 승인 대기·차단 안내 |
| 403 | CSRF_FAILED | CSRF 또는 요청 출처 검증 실패 |
| 409 | EMAIL_ALREADY_EXISTS | 이메일 고유 제약 충돌 |
| 429 | LOGIN_RATE_LIMITED / IP_RATE_LIMITED | 이메일 잠금 또는 IP 제한. Retry-After 헤더도 제공 |
| 400 | INVALID_RESET_TOKEN / CODE_EXPIRED / CODE_MISMATCH | 인증 증거 불일치·만료 |
| 422 | VALIDATION | DTO 입력값 오류 |
| 500/503 | INTERNAL_ERROR / SERVICE_UNAVAILABLE | 서버·DB·외부 서비스 오류 |

기존 회원가입은 EMAIL_TAKEN, INVALID_TOKEN 등을 쓴다. 통합 시 양쪽 담당자가 오류 코드 대응표를 정하고 프론트와 서버를 함께 바꾼다. 전부 EMAIL_ALREADY_EXISTS로 일괄 치환하지 않는다. client.ts는 204 본문 없는 성공도 처리해야 한다.

## 8 DB 구조 제안

### user_sessions

| 컬럼 | 자료형·제약 | 의미 |
| --- | --- | --- |
| session_id | UUID PK, DB 기본 생성 | 세션 행 식별자. 쿠키 토큰과 다름 |
| token_hash | TEXT NOT NULL UNIQUE | 쿠키 토큰의 해시 |
| user_id | UUID NOT NULL FK users.user_id | 로그인 회원 |
| csrf_token | TEXT NOT NULL | 서버 세션에 연결한 CSRF 토큰. API로 전달 가능, 인증 토큰은 아님 |
| created_at | TIMESTAMPTZ NOT NULL | 로그인 시각 |
| last_activity_at | TIMESTAMPTZ NOT NULL | 마지막 인정 활동 |
| idle_expires_at | TIMESTAMPTZ NOT NULL | 비활동 만료 |
| absolute_expires_at | TIMESTAMPTZ NOT NULL | 생성+8시간 |
| revoked_at | TIMESTAMPTZ NULL | 폐기 시각 |

user_id 인덱스로 전체 세션 폐기를 지원한다. 만료·폐기된 행은 보관 기간을 정한 뒤 정리 작업으로 삭제한다. 정리 전에도 인증 시 만료 여부를 검사한다.

### 제한 기록

- login_failures: id, email_key, failed_at. 최근 15분의 실제 검증 실패 이벤트를 저장한다. email_key는 정규화 이메일의 HMAC 등으로 저장 가능하며 이메일+시각 인덱스를 둔다.
- login_locks: email_key PK, blocked_until. 성공·실패 요청의 원자 처리를 위해 같은 이메일 잠금을 사용한다.
- login_ip_requests: id, ip_key, requested_at. 최근 60초 로그인 요청 수를 집계하며 IP+시각 인덱스를 둔다.
- 첫 요청에서 행이 없는 경우에도 안전하도록 UPSERT 또는 PostgreSQL advisory lock을 쓴다. 단순 SELECT 후 INSERT만으로 동시성 보호를 끝내지 않는다.
- 같은 이메일의 요청은 순서를 보장해 동시 5회 실패가 누락되지 않게 한다. IP 제한도 동일 IP 단위로 원자 집계한다.

### 비밀번호 재설정 기록

purpose가 PASSWORD_RESET인 인증 전용 기록을 사용한다. 제안 컬럼은 id, user_id, email, code_hash, code_expires_at, failed_count, locked_until, reset_token_hash, reset_token_expires_at, consumed_at이다. 가입 인증과 테이블을 분리하거나 기존 테이블에 purpose를 도입하되, 기존 email PK 구조를 그대로 재사용해 가입 인증을 덮어쓰지 않는다. 메일 발송 제한 정책은 기존 메일러와 함께 적용한다.

## 9 CRUD와 트랜잭션

CRUD는 DB 데이터의 생성(Create), 조회(Read), 수정(Update), 삭제(Delete)를 뜻한다. 인증에서는 실제 행 삭제 대신 revoked_at을 기록하는 논리적 폐기를 사용한다.

| 사용자 동작 | C 생성 | R 조회 | U 수정·폐기 | D 물리 삭제 |
| --- | --- | --- | --- | --- |
| 가입 | users | 인증 증거·이메일 | 인증 증거 소비 | 없음 |
| 로그인 성공 | user_sessions, IP 요청 | users·제한 | 실패 기록 초기화·필요 시 해시 재생성 | 성공 시 해당 실패 이벤트 정리 가능 |
| 로그인 실패 | 실패 이벤트·IP 요청 | users·최근 실패 | 5번째에서 잠금 설정 | 없음 |
| 내 정보 확인 | 없음 | 세션·users | 활동 인정 요청일 때만 세션 시간 갱신 | 없음 |
| 자동 조회 | 없음 | 세션·업무 데이터 | 활동 시간 갱신 안 함 | 없음 |
| 일반 로그아웃 | 없음 | 현재 세션 | 현재 세션 revoked_at | 없음 |
| 프로필 수정 | 없음 | 세션·본인 회원 | 허용된 프로필 필드 | 없음 |
| 비밀번호 변경 | 없음 | 세션·현재 해시 | 새 해시·모든 세션 폐기 | 없음 |
| 재설정 | 재설정 인증 기록 | 인증 증거·users | 새 해시·인증 소비·모든 세션 폐기 | 없음 |
| 보관 기간 정리 | 없음 | 만료 기록 | 없음 | 오래된 세션·제한·인증 기록 |

가입은 회원 생성과 인증 소비를 같은 트랜잭션으로 처리한다. 비밀번호 변경·재설정은 새 해시 저장과 모든 세션 폐기를 같은 트랜잭션으로 처리한다. 실패 기록은 의도된 401/429에서도 커밋되어야 하며, 예외 처리의 일괄 롤백으로 사라지지 않도록 한다. 예상 밖 서버·DB 오류는 실패 기록 추가 없이 롤백한다.

로그인과 비밀번호 변경·재설정은 동일 회원에 대한 잠금 규칙을 공유한다. 이전 비밀번호를 확인한 로그인 요청이 비밀번호 변경 이후 새 세션을 만드는 경쟁을 막는다. 잠금 순서를 통일해 교착을 피한다. 쿠키는 DB 커밋에 성공한 후 응답에 붙인다.

## 10 동작 순서

### 로그인

1. LoginPage가 email·password를 auth.ts를 통해 전송한다.
2. 서버가 이메일을 정규화하고 IP 제한 및 이메일 잠금을 검사한다.
3. 회원을 조회하고 Argon2id로 검증한다. 없는 이메일은 더미 해시로 검증해 처리 시간 차이를 줄인다.
4. 잘못된 비밀번호면 실패 이벤트를 커밋하고 401을 반환한다. 5번째는 잠금을 설정하고 429를 반환하는 안이다.
5. 올바른 비밀번호면 승인·차단 상태를 확인한다. 허용되지 않은 계정에는 세션을 발급하지 않는다.
6. 이메일 실패 기록 초기화와 세션 생성을 커밋한다. 기존 다른 기기 세션은 유지한다.
7. Set-Cookie와 사용자·CSRF·만료 정보를 반환한다. AuthProvider가 메모리 상태를 갱신한다.
8. 원래 목적지 또는 /profile로 이동한다.

### 새로고침과 만료

앱 시작 시 /me로 DB 세션을 확인한다. 확인 중에는 로그인 화면으로 먼저 튀지 않게 loading 화면을 표시한다. /me 자체는 활동을 연장하지 않는다. 서버가 session의 idle·absolute·revoked 및 회원 상태를 매번 검사한다. 401은 인증 상태를 해제하고 로그인으로 안내하되 403·429·네트워크 오류를 전부 로그아웃으로 취급하지 않는다. 자동 폴링에서 반복 경고나 이동이 발생하지 않게 공통 처리한다.

### 활동 갱신

명시적인 조회·저장 요청에 프론트가 X-Session-Activity: user를 붙이는 안이다. 공통 클라이언트의 기본값은 background로 두고 페이지에서 활동 여부를 지정한다. 서버는 유효한 세션으로 허용된 요청이 성공한 경우에만 last_activity_at과 idle_expires_at을 갱신한다. 자동 폴링·/me에는 갱신 표시를 붙이지 않는다.

네트워크 요청 없이 폼을 작성하는 활동도 반영하기 위해 실제 키 입력·클릭 후 최대 60초에 한 번 /activity를 보내는 안이다. 아무 활동 없이 타이머만으로 보내지 않는다. 서버는 브라우저의 진짜 사람 활동을 완벽히 증명할 수 없으므로 이 표시는 UX 정책이며 보안 증명이 아니다. 절대 8시간 제한은 항상 서버에서 적용한다.

갱신식: idle_expires_at = min(서버 현재 시각 + 30분, absolute_expires_at). 폐기나 만료 후에는 UPDATE 조건으로 갱신을 거절한다. 한 탭에서 유효한 활동을 하면 같은 쿠키를 쓰는 다른 탭도 동일 세션을 사용한다.

### 로그아웃

CSRF 확인 후 현재 토큰의 세션만 폐기하고 커밋한다. 쿠키를 같은 이름·경로로 삭제하고 프론트 상태를 비운다. 반복 로그아웃은 204로 처리할 수 있게 하되 유효한 세션이 존재하는 요청의 CSRF 검사는 생략하지 않는다. 다른 기기의 세션은 유지한다. 같은 브라우저의 다른 탭은 다음 API의 401 또는 BroadcastChannel 알림으로 상태를 맞춘다.

### 비밀번호 변경과 재설정

변경은 내 프로필에서만 시작하고 현재 세션·현재 비밀번호를 검증한다. 재설정은 세션 없이 이메일 인증으로 진행한다. 두 흐름 모두 새 비밀번호 해시 저장과 전체 세션 폐기를 원자 처리한다. 완료 후 로그인 화면으로 이동한다. 재설정 인증 토큰은 일회용이고 가입 토큰으로 대체할 수 없다.

## 11 CSRF와 쿠키 처리

인증된 상태 변경 요청은 세션에 연결한 CSRF 토큰을 X-CSRF-Token 헤더로 보내고 서버에서 비교한다. 로그인 응답과 인증된 /me에서 CSRF 토큰을 받아 메모리에 보관한다. 다른 탭도 /me에서 자신의 공유 세션 토큰을 얻는다. 응답은 Cache-Control: no-store로 제공한다.

로그인·가입·메일 발송처럼 세션이 없는 POST도 허용된 Origin, JSON Content-Type 및 제한된 CORS 정책으로 보호한다. 개발 프록시 구성과 운영 웹 Origin을 설정에서 구분한다. Origin 없는 API 호출은 허용 여부를 명시하며 브라우저 전용 API에서는 거절하는 안이다. SameSite 하나만으로 모든 CSRF 방어를 끝내지 않는다. 프록시 환경의 실제 IP는 신뢰하는 프록시 설정을 통해서만 복원하고 임의의 X-Forwarded-For를 그대로 믿지 않는다.

참고: [OWASP 세션 관리](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html), [OWASP CSRF 방어](https://cheatsheetseries.owasp.org/cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.html).

## 12 팀원 코드 통합 전에 해결할 차이

| 확인된 차이 | 개발 전 처리 |
| --- | --- |
| 현재 로그인 브랜치 백엔드가 공통 초기 코드 | 프론트 변경 보존 후 feat/sign-up을 검토·통합 |
| 팀원 가입은 approved_at NULL인 PENDING 회원 생성 | 승인된 회원만 로그인하는 안을 문서화. 관리자 승인 담당과 연동 확인 |
| 팀원은 차단되지 않은 회원에만 이메일 부분 UNIQUE 적용 | 합의된 전체 이메일 UNIQUE와 다름. 차단 회원 재가입 정책을 확정하고 데이터 중복 검사 후 제약 조정 |
| 팀원은 모든 IntegrityError를 EMAIL_TAKEN으로 처리 | 이메일 고유 제약 위반만 중복으로 매핑, 다른 DB 오류는 별도 처리 |
| 기존 마이그레이션과 ORM의 enum 이름·시간 타입 차이 | 실제 0001→0002 적용 결과와 모델을 비교. 초기 파일 재작성 대신 후속 마이그레이션으로 보정 |
| 회원가입 프론트에 생일·휴대폰·개인정보 동의가 추가됨 | 필수 수집 범위와 서버 동의 검증은 가입 담당자와 확인 |
| 기존 refresh_token 구조 | 세션으로 대체하되 삭제는 별도 합의. 새 로그인에서 사용하지 않음 |
| 'ntt를 브라우저 파일에 넣기'의 원래 의미 미확인 | 세션 ID의 HttpOnly 쿠키 저장으로 설계. JWT/localStorage 요구였다면 재논의 |

현재 로컬에 중첩된 teamproject1 폴더도 있다. 실제 작업 루트는 /Users/kimheejun/teamproject1이며 중첩 폴더에서 개발하지 않는다.

## 13 구현 순서와 완료 조건

| 단계 | 작업 | 완료 조건 |
| --- | --- | --- |
| 1 | 프론트 변경 보존, 회원가입 백엔드 통합, API·승인 정책 정합성 확인 | 기존 가입 시나리오 정상, 소스·DB 상태 확인 |
| 2 | 세션·실패 기록·재설정 모델과 마이그레이션 | 새 DB와 기존 개발 DB에서 마이그레이션 성공 |
| 3 | 공통 세션 의존성·쿠키·CSRF·오류 형식 | 세션 위조·만료·폐기 거절 |
| 4 | 로그인·me·현재 로그아웃 API | 다중 세션, 탭 공유, 현재 세션만 폐기 확인 |
| 5 | AuthProvider·레이아웃·로그인 폼 연결 | 로그인 후 새로고침 유지, 미로그인 보호 경로 차단 |
| 6 | 30분·8시간·사용자 활동 처리 | 폴링 제외, 작성 중 활동 반영, 8시간 초과 갱신 거절 |
| 7 | 프로필 비밀번호 변경·메일 재설정 | 변경/재설정 후 모든 기존 세션 거절 |
| 8 | 통합·동시성 검증·실행 안내 | 아래 검증표 통과, 빌드 성공, 환경변수 예시 갱신 |

## 14 검증 계획

- backend/tests/test_login.py: 성공, 잘못된 이메일/비밀번호, 승인 대기, 차단, 5회 실패, 잠금 중 시간 불변, 15분 경계, 성공 초기화, 서버 오류 제외.
- backend/tests/test_sessions.py: 비활동 30분·절대 8시간 경계, 활동 갱신·자동 조회 제외, 만료 후 부활 금지, 다중 세션, 현재 로그아웃.
- backend/tests/test_passwords.py: 현재 비밀번호 검증, 새 정책 검사, reset_token 만료·일회용·목적 구분, 모든 세션 폐기, DB 실패 롤백.
- backend/tests/test_auth_concurrency.py: 동시 5회 실패, IP 31번째 요청, 로그인과 비밀번호 변경 경쟁, 로그아웃과 활동 갱신 경쟁. PostgreSQL에서 수행한다.
- backend/tests/test_signup.py: 이메일 전체 UNIQUE 충돌, 인증 소비 원자성, 실패 후 유효 인증 재사용. 가입 담당 범위와 협업한다.
- frontend LoginPage·ProtectedRoute·비밀번호 폼 테스트: 로딩, 중복 제출, 401/403/429 메시지, 새로고침, 본문 없는 204 처리.
- 실제 브라우저: 로그인·회원가입 화면 레이아웃, 두 탭 공유, 두 브라우저 독립 세션, 로그아웃, CSRF 거절, 쿠키 속성 확인.
- 시간을 기다리는 대신 제어 가능한 서버 시계로 만료 경계를 검증한다. 현재 프론트 도구는 Node 20과 테스트 의존성의 호환 문제가 있으므로 지원되는 Node 버전에서 테스트한다.

## 15 문서를 읽는 순서

처음에는 4장의 전체 연결을 보고 6장의 화면 구조를 확인한다. 실제 구현은 5장의 파일별 책임에 맞춰 13장 순서로 진행한다. API 요청·응답은 7장, DB 변경은 8~9장, 예외·보안·동시성은 10~14장에서 확인한다. 이 문서는 계획서이며 모든 제안이 이미 구현되었다는 의미는 아니다.
