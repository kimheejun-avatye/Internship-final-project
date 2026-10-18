# 회원가입·로그인 전용 브랜치

`codex/login-only`는 main(`5ed8191`)을 기준으로 회원가입과 로그인·비밀번호 변경·비밀번호 찾기만 추가한 브랜치다. main 자체와 기존 codex/login 브랜치는 변경하지 않는다.

## 가져온 원본

- 회원가입 백엔드: feat/sign-up `02caccc`의 main 대비 변경만 사용.
- 회원가입 화면: feat/frontend-signup-api `3d7beed`에서 가입 화면과 필수 공통 파일만 사용.
- 로그인 담당 구현: `3ce2f33`에서 세션·로그인·비밀번호 변경·찾기 및 필수 설정·테스트만 사용.
- 예약·회의실·캘린더·관리자·Slack 알림 구현과 임시 데이터는 추가하지 않았다. main에 원래 있는 공통 뼈대와 초기 DB 이력은 보존한다.

## 실행 구조

```text
backend/app/
├── api/routes/auth.py       # 회원가입 담당 원본
├── api/routes/login.py      # 로그인·세션·로그아웃
├── api/routes/password.py   # 비밀번호 변경·찾기
├── services/                # 가입 원본과 인증 업무 로직
├── schemas/                 # 가입 원본과 로그인·비밀번호 DTO
├── models/                  # 가입·세션·제한·재설정 모델
├── core/                    # 공통 설정·보안
└── db/                      # DB 연결
frontend/src/
├── main.tsx / App.tsx
├── auth/                    # 로그인 상태·보호 라우트
├── layouts/                 # 인증·계정 화면 틀
├── pages/auth/              # 회원가입·로그인·비밀번호 찾기
├── pages/profile/           # 비밀번호 변경
├── shared/                  # 통신·타입·hooks
└── styles/                  # 가입·인증 화면 스타일
```

회원가입의 차단 이메일 재가입 정책·users 인덱스·승인 정책을 변경하지 않았다. 가입 후 승인 대기, 외부 승인 후 로그인하는 기존 계약을 따른다. 승인 기능은 포함하지 않는다.

실행과 검증은 [로그인 구현 안내](docs/design/login-implementation.md), 변경 범위는 [브랜치 범위](docs/design/login-pr-readiness.md)를 참고한다.
