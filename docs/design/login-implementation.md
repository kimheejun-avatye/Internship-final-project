# 로그인 담당 구현 및 실행 안내

## 범위

로그인·세션 관리·비밀번호 변경·비밀번호 찾기만 담당한다. 가입·승인·차단·프로필 이름 수정·다른 팀 기능은 변경하지 않는다. [개발 계획](login-development-plan.md), [PR 검증](login-pr-readiness.md)을 함께 본다.

## 실행

Python 3.10 이상, uv, PostgreSQL, 프런트 package.json의 Node engines에 맞는 Node를 사용한다.

루트 .env.example을 .env로 복사하고 PostgreSQL 값과 32자 이상 무작위 SECRET_KEY를 설정한다. .env는 Git에 올리지 않는다. frontend/.env.local에 BACKEND_URL=http://127.0.0.1:8001을 지정하면 아래 포트와 연결된다.

```bash
# 새 DB 또는 기존 로그인/팀 DB 기준 (백업 후 적용)
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --host 127.0.0.1 --port 8001 --no-proxy-headers
```

```bash
cd frontend
npm ci
npm run dev -- --host 127.0.0.1 --port 5174
```

/login은 로그인, /password/reset은 비밀번호 찾기, /profile은 비밀번호 변경 화면이다. 로그인 성공과 기존 로그인 복원 후 기본 이동은 /reservations다. /signup은 기존 담당자 화면을 그대로 사용한다. 최신 developer의 예약·캘린더·관리자 화면은 ProtectedRoute와 팀 AppLayout 아래에 연결했다. 팀 화면의 임시 데이터는 유지한다.

회원가입은 기존대로 승인 대기 계정을 만든다. 승인 기능은 담당자가 처리하며 로그인 코드는 approved_at·blocked_at 결과만 읽는다. 승인 CLI나 이름 수정 API는 이번 범위에 없다.

SMTP 미설정 개발 환경에서는 재설정 코드가 서버 로그에 출력된다. 실제 이메일 전달과 운영 HTTPS·SMTP 설정은 별도 환경에서 확인해야 한다.

## 회원가입과 호환

- 이메일 정규화·Argon2id·새 비밀번호 조건은 기존 가입 코드에서 재사용한다.
- 차단 이메일 재가입 허용 정책과 users_email_active_uniq를 유지한다.
- 과거 차단 계정과 새 계정이 같은 이메일이어도 로그인·찾기는 현재 계정을 정확히 선택한다.
- 재설정 증명은 user_id에 연결되므로 과거 계정의 증명으로 재가입 계정 비밀번호를 바꿀 수 없다.
- 가입 DTO·서비스·API·화면·mailer·공통 HTTP client를 변경하지 않는다. 내 DTO·메일러·클라이언트·스타일은 별도 파일이다.

## DB 이력 주의

login_0003은 인증 전용 테이블만 추가한다. 팀 캘린더 0003과 연결하는 merge_0004를 추가했으며 기존 revision과 users 인덱스는 변경하지 않는다. 단일 head로 합쳐지지만 기존 개발 DB에는 자동 적용하지 않았다.

이전에 로그인 전용 0003 또는 이메일 전체 UNIQUE를 적용한 로컬 DB는 팀의 같은 번호 DB와 구조가 다를 수 있다. 이 DB에 즉시 upgrade를 실행하거나 stamp하지 않는다. 백업과 실제 테이블·인덱스 확인 후 별도 전환해야 하며 이번 작업에서 기존 개발 DB를 변경하지 않았다.

## 검증

이름이 _test로 끝나는 별도 PostgreSQL DB를 TEST_DATABASE_URL로 지정한 후 백엔드에서 pytest -q를 실행한다. 테스트가 해당 DB 데이터를 초기화하므로 개발 DB를 지정하지 않는다. 프런트는 npm test와 npm run build를 실행한다.

세션은 비활동 30분·절대 8시간, 일반 로그아웃은 현재 세션만, 비밀번호 변경·찾기 완료는 해당 계정 전체 세션 폐기다. 자동 me 조회는 연장하지 않는다. HttpOnly 쿠키·Origin/JSON·CSRF 및 단계별 요청 제한은 내 인증 API에만 적용된다.

로컬 화면은 현재 5175, 백엔드는 8002에서 실행한다. frontend/.env.local의 BACKEND_URL과 루트 .env의 APP_ORIGINS가 실제 접속 주소와 맞아야 한다. 테스트는 별도 DB를 사용한다.
