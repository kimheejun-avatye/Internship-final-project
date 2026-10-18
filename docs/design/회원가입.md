# 로그인·비밀번호 변경·비밀번호 찾기 개발 계획서

대상: teamproject1, codex/login-only. 현재 담당 범위는 아래 세 기능과 그에 필요한 세션 관리다. 기존 문서의 회원가입 정책 변경·프로필 이름 수정·전체 팀 기능 통합 계획은 이 문서로 정정한다.

## 담당 범위

- 로그인: 이메일·비밀번호 검증, 세션 발급·조회·만료·활동 갱신·현재 세션 로그아웃.
- 비밀번호 변경: 로그인 세션과 현재 비밀번호 확인, 새 비밀번호 저장, 해당 계정의 모든 세션 종료.
- 비밀번호 찾기: 이메일 인증번호 → 재설정 전용 일회용 증명 → 새 비밀번호 저장, 해당 계정의 모든 세션 종료.

회원가입·승인·차단·이름 수정·예약·회의실·캘린더·관리자 기능의 코드는 담당자의 영역이다. 기존 정책·API를 재사용하며 변경하지 않는다.

## 10가지 정책

| 번호 | 항목 | 결정 |
|---|---|---|
| 1 | 인증 방식 | JWT·Refresh Token 없이 서버 세션과 HttpOnly 쿠키 사용. 원문은 쿠키, 해시는 서버 DB |
| 2 | 비활동 만료 | 마지막 인정 활동부터 30분 |
| 3 | 절대 만료 | 최초 로그인부터 8시간. 활동으로 초과 연장하지 않음 |
| 4 | 활동 인정 | 실제 사용자 동작은 activity 요청으로 연장. 자동 조회·초기 me 조회·실패 요청은 연장하지 않음 |
| 5 | 기기·로그아웃 | 기기별 별도 세션. 같은 브라우저 탭은 쿠키 공유. 일반 로그아웃은 현재 세션만 종료 |
| 6 | 비밀번호 실패 제한 | 이메일별 최근 15분 5회 실패 → 5분 잠금. 잠금 중 연장 없음. 성공 시 실패 기록 초기화 |
| 7 | IP 제한 | 로그인 요청 최근 1분 30회. 변경·재설정에도 단계별 제한 적용 |
| 8 | 비밀번호 변경 | 현재 세션·현재 비밀번호·새 비밀번호 정책 검사. 비밀번호 저장과 전체 세션 폐기를 같은 트랜잭션으로 처리 |
| 9 | 비밀번호 찾기 | 이메일 인증 5분, 재설정 증명 15분·일회용·계정 ID 연결. 가입 인증과 용도 분리. 완료 시 전체 세션 폐기 |
| 10 | 가입 기능과 계약 | 가입 담당자의 이메일 정규화·Argon2id·승인 대기·차단 상태·비밀번호 조건·부분 UNIQUE 정책 그대로 사용 |

## 회원가입과 연결하는 계약

- 가입 담당자의 users 모델, signup 서비스, signup DTO와 API, 메일러·공통 클라이언트·가입 화면을 변경하지 않는다.
- 승인 대기 계정은 로그인 거절, 승인된 비차단 계정만 세션 생성. 승인·차단 기능 자체는 구현하지 않는다.
- 기존 정책은 비차단 계정에만 이메일 UNIQUE를 적용한다. 차단 이력과 재가입 계정이 같은 이메일을 가질 수 있다.
- 로그인은 현재 비차단 계정을 우선 선택한다. 그 계정의 비밀번호가 틀렸다고 과거 차단 계정의 비밀번호로 재시도하지 않는다.
- 비밀번호 찾기는 비차단 계정만 대상으로 한다. 증명을 계정 ID에 연결해 과거 계정의 증명으로 새 계정을 변경하지 못하게 한다.
- 새 비밀번호 정책은 기존 SignupIn 검증을 호출해 재사용한다. 해시 생성·검증도 기존 security 함수를 사용한다.
- 가입 API와 로그인 API의 연동만 테스트한다. 승인 단계는 테스트에서 기존 필드 변경을 모의하며 운영 승인 기능은 추가하지 않는다.

## 실제 파일 구조

```text
backend/app/
├── api/
│   ├── dependencies.py           # 세션·CSRF 검증
│   ├── session_security.py       # 로그인·비밀번호 경로 전용 HTTP 보호
│   └── routes/
│       ├── login.py
│       └── password.py
├── schemas/
│   ├── login.py                  # 가입 schemas/auth.py와 분리
│   └── password.py
├── services/
│   ├── auth.py
│   ├── sessions.py
│   ├── login_limits.py
│   ├── passwords.py
│   ├── password_mailer.py         # 가입 mailer.py와 분리
│   └── clock.py
└── models/
    ├── user_sessions.py
    ├── login_attempts.py
    └── password_reset_verifications.py

frontend/src/
├── auth/                         # AuthProvider·ProtectedRoute
├── layouts/                      # 내 인증 화면과 비밀번호 변경 화면의 틀
├── pages/auth/                   # LoginPage·PasswordResetPage
├── pages/profile/                # 비밀번호 변경 폼과 현재 계정 표시
├── shared/api/
│   ├── auth.ts
│   ├── password.ts
│   └── session-client.ts         # 가입 client.ts는 그대로 유지
├── shared/hooks/useSessionActivity.ts
├── shared/types/auth.ts
└── styles/session.css
```

## API

| 메서드 | 경로 | 역할 |
|---|---|---|
| POST | /api/auth/login | 로그인·세션 쿠키 발급 |
| GET | /api/auth/me | 세션·현재 사용자 조회, 비활동 만료 연장 없음 |
| POST | /api/auth/activity | 실제 사용자 활동 갱신 |
| POST | /api/auth/logout | 현재 세션 종료·쿠키 제거 |
| POST | /api/auth/password/change | 현재 비밀번호 확인 후 변경 |
| POST | /api/auth/password/reset/send-code | 재설정 인증번호 요청 |
| POST | /api/auth/password/reset/verify-code | 인증번호 확인·일회용 재설정 증명 발급 |
| POST | /api/auth/password/reset | 증명 검증 후 새 비밀번호 저장 |

## PR과 DB 연결

main의 0001과 회원가입의 0002는 수정하지 않는다. 로그인 전용 login_0003은 세션·요청 제한·재설정 테이블만 추가하며 users 인덱스는 바꾸지 않는다.

main.py의 라우터 등록, React App/main의 내 화면 연결, 환경설정·의존성·테스트 초기화 등 공통 연결 지점에는 필요한 변경이 있다. 다른 기능의 업무 로직은 그대로다. 이 브랜치에는 예약·달력·관리자 구현을 가져오지 않는다.

완료 기준은 정상·실패·잠금·만료·CSRF·동시 요청, 비밀번호 변경/재설정 후 세션 종료, 가입→승인 대기→외부 승인→로그인, 차단 이력과 재가입 계정 구분, 기존 팀 테스트 통과다. 미래의 모든 병합 충돌을 보장하지 않으며 PR 직전 대상 브랜치 최신 상태로 다시 확인한다.

## developer 통합 반영

developer ddb56f9를 병합했다. 로그인 성공·기존 세션 복원 후 기본 페이지는 /reservations다. 팀 공통 AppLayout 아래 캘린더·예약·관리자·비밀번호 변경 경로를 보호 라우트로 연결한다. 회원가입 정책·팀 서비스는 변경하지 않는다. 기존 login_0003과 팀 0003을 유지하고 merge_0004로 연결했다. 앞의 main 기준 전용 범위 설명보다 이 통합 결과가 우선한다.
