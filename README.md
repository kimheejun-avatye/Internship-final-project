# 회의실 예약 프로젝트

백엔드는 FastAPI, DB는 PostgreSQL을 사용하며 Supabase는 사용하지 않는다. 회원가입과 세션 로그인 및 비밀번호 변경·재설정이 구현되어 있으며, 실행·검증 방법은 아래 로그인 개발 안내를 따른다.

## 로컬 PostgreSQL 실행

처음 설정할 때 프로젝트 루트에서 환경변수 예시 파일을 복사한다.

```bash
cp .env.example .env
```

루트 `.env`에서 `POSTGRES_PORT`, `POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`를 설정한 뒤 실행한다.

```bash
docker compose up -d
```

Docker Compose는 루트 `.env`를 자동으로 읽는다. 필수 변수가 없거나 비어 있으면 실행 시 오류가 발생한다. 터미널에 같은 환경변수가 설정되어 있으면 터미널 값이 우선한다. `backend/.env`는 이 설정에 사용하지 않는다.

예시 설정의 접속 주소는 `localhost:5433`이다. `POSTGRES_PORT`는 호스트 접속 포트이며 컨테이너 내부 포트는 `5432`로 고정된다. `.env`는 Git에서 제외하고, 팀에 공유할 변수 목록은 `.env.example`에서 관리한다.

데이터는 Docker 볼륨에 보존된다. DB 이름·계정·비밀번호는 볼륨 초기화 시 적용되므로, 이미 생성된 DB는 `.env` 수정만으로 변경되지 않는다.

## DB 마이그레이션

루트 `.env` 설정 및 PostgreSQL 기동 후 실행한다. Python 3.9 이상이 필요하다.

```bash
bash backend/scripts/migrate.sh
```

스크립트가 전용 가상환경과 의존성을 준비하고 Alembic 마이그레이션을 적용한다.
[ERD 및 마이그레이션 실행 안내](docs/design/database.md)에서 테이블별 컬럼과 제약, 실행 방법을 확인할 수 있다.

## 폴더 구조

```text
teamproject1/
├── backend/
│   ├── app/
│   │   ├── api/          # 팀 회원가입·회의실 API + 로그인·비밀번호·프로필 API
│   │   ├── schemas/      # 요청·응답 형식
│   │   ├── services/     # 인증 업무 로직·팀 예약/캘린더 스켈레톤
│   │   ├── models/       # 팀 모델 + 세션·로그인 제한·재설정 모델
│   │   ├── core/         # 설정·보안·공통 오류
│   │   └── db/           # DB 연결
│   ├── migrations/       # 0001 → 0002 → 팀 캘린더 0003 → 로그인 0004
│   └── tests/
├── frontend/src/
│   ├── main.tsx          # React 진입점
│   ├── App.tsx           # 팀 화면과 인증 화면 라우팅
│   ├── auth/             # 세션 상태·보호 라우트
│   ├── layouts/          # 인증 화면 공통 틀 AuthLayout
│   ├── components/       # 팀 AppLayout·Logo
│   ├── pages/            # auth·profile·reservation·calendar·admin
│   ├── shared/           # API·타입·hooks
│   ├── mocks/            # 팀 예약·캘린더·관리자 화면의 기존 임시 데이터
│   └── styles/
└── docs/
    ├── design/
    └── collaboration/
```

실제 진입점은 `frontend/src/main.tsx`다. 팀 공통 AppLayout에 세션 로그아웃을 연결하고, 기존 예약·캘린더·관리자 메뉴와 화면을 유지한다. 예약·캘린더 화면의 임시 데이터를 실제 API로 바꾸는 작업은 해당 기능 담당자의 범위다.

[구조 설명](docs/design/architecture.md) · [DB 설계](docs/design/database.md) · [로그인 PR 검증](docs/design/login-pr-readiness.md)

## 로그인 개발

[로그인 구현 및 실행 안내](docs/design/login-implementation.md)에서 환경 설정, 세션 정책, API, 테스트, 회원 승인 방법을 확인한다.
