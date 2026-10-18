# 회의실 예약 — 로그인과 developer 통합

작업 폴더는 login-only, 브랜치는 codex/login-only다. 회원가입·세션 로그인 전용 e087f49에 developer ddb56f9를 머지했다. main·developer 원격 브랜치와 별도 teamproject1 폴더의 codex/login은 변경하지 않는다.

## 로그인 후 이동

- 로그인 성공: 항상 /calendar로 이동한다.
- 유효한 세션으로 /login 또는 /password/reset 접근: /calendar로 이동한다.
- 캘린더·예약·관리자·비밀번호 변경 화면은 ProtectedRoute와 팀 공통 AppLayout으로 연결한다.
- 팀 메뉴의 로그아웃 버튼은 서버의 현재 세션 종료를 호출한다. 비밀번호 변경 메뉴는 /profile이다.
- /signup은 기존 담당자의 화면·API·정책을 그대로 사용한다.

## 구조

```text
backend/app/
├── api/            # 로그인·비밀번호·가입·회의실 HTTP 연결
├── services/       # 인증 업무 로직 + 팀 예약/캘린더 서비스
├── schemas/        # 요청·응답 형식
├── models/         # 가입·인증 + 팀 회의실·예약·참석자·리마인더
├── core/           # 설정·보안
└── db/             # DB 연결
frontend/src/
├── main.tsx / App.tsx
├── auth/           # 세션 상태·보호 라우트
├── layouts/        # AuthLayout
├── components/     # 팀 공통 AppLayout·Logo
├── pages/          # auth·profile·calendar·reservation·admin
├── shared/         # API·타입·hooks
├── mocks/          # 기존 팀 화면의 임시 데이터
└── styles/
```

## DB 이력

기존 login_0003과 팀 캘린더 0003을 유지하고 merge_0004로 합쳤다. users 정책·인덱스는 변경하지 않는다. 새 DB·로그인 DB·팀 DB에서 upgrade head가 같은 단일 head로 이어지는 것을 별도 DB에서 검증했다. 기존 개발 DB에는 자동 적용하지 않았다.

## 확인 결과

백엔드 85개·프런트 26개 테스트, TypeScript 검사·프로덕션 빌드·인증 코드 정적 검사 통과. 캘린더 화면은 기존 팀 임시 데이터를 유지하며 실제 API로의 교체는 이번 머지에서 구현하지 않는다.

[실행 안내](docs/design/login-implementation.md) · [머지 검증](docs/design/login-pr-readiness.md)
