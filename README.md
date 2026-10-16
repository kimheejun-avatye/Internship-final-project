# 회의실 예약 프로젝트

백엔드는 FastAPI, DB는 PostgreSQL을 사용하며 Supabase는 사용하지 않는다. 애플리케이션은 개발 전 폴더 구조를 정리한 상태이며, 로컬 PostgreSQL 실행 설정은 준비되어 있다.

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

## 폴더 구조

```text
project2/
├── README.md                    # 프로젝트 안내와 파일 위치
├── .gitignore                   # Git 제외 규칙 작성 예정
├── compose.yaml                 # 로컬 PostgreSQL 실행 설정
├── docs/
│   ├── design/                  # 구조·ERD·인증·설계 결정
│   └── collaboration/           # 실행 방법·작업 분담·API 약속
├── backend/
│   ├── pyproject.toml           # Python 의존성 설정용
│   ├── .env.example             # 환경변수 예시 작성용
│   ├── alembic.ini              # DB 마이그레이션 설정용
│   ├── migrations/
│   │   ├── env.py
│   │   └── versions/            # 스키마 변경 이력
│   ├── app/
│   │   ├── main.py              # FastAPI 시작과 라우터 연결
│   │   ├── api/routes/          # HTTP 요청·응답
│   │   │   ├── auth.py          # 가입·로그인·로그아웃·재발급
│   │   │   ├── users.py         # 사용자 정보
│   │   │   ├── rooms.py         # 회의실
│   │   │   └── reservations.py  # 예약
│   │   ├── schemas/             # 요청·응답 형식
│   │   │   ├── auth.py
│   │   │   ├── users.py
│   │   │   ├── rooms.py
│   │   │   └── reservations.py
│   │   ├── services/            # 업무 규칙과 처리 순서
│   │   │   ├── auth.py
│   │   │   ├── refresh.py       # Refresh Token 처리
│   │   │   ├── users.py
│   │   │   ├── rooms.py
│   │   │   └── reservations.py
│   │   ├── models/              # ERD의 네 테이블 정의
│   │   │   ├── users.py
│   │   │   ├── refresh_token.py
│   │   │   ├── rooms.py
│   │   │   └── reservations.py
│   │   ├── core/
│   │   │   ├── config.py        # 환경변수와 서버 설정
│   │   │   ├── security.py      # 비밀번호·인증 보안 도구
│   │   │   └── exceptions.py    # 공통 오류 처리
│   │   └── db/
│   │       ├── base.py          # 모델 공통 기반
│   │       └── session.py       # DB 연결과 트랜잭션 지원
│   ├── tests/                   # 인증·사용자·회의실·예약·DB 테스트용
│   └── scripts/
│       └── seed.py              # 개발용 초기 데이터 작성용
└── frontend/src/
    ├── main.ts                  # 화면 앱 시작
    ├── app/                     # 화면 전환·상태·스타일
    ├── pages/
    │   ├── auth/                # 가입·로그인
    │   ├── profile/             # 사용자 정보
    │   ├── rooms/               # 회의실·예약 화면
    │   └── calendar/            # 예약 달력
    └── shared/                  # 공통 API 호출·타입·화면 도구
```

Python 패키지의 `__init__.py`는 트리에서 생략했다. 프런트엔드는 기존 사이트의 파일 배치를 따른 자리이며 빌드 도구·프레임워크 설정은 아직 없다.

## 파일을 찾는 기준

| 수정할 내용 | 위치 |
|---|---|
| API 주소·상태 코드·응답 | `backend/app/api/routes/` |
| 입력·응답 데이터 형식 | `backend/app/schemas/` |
| 기능의 처리 순서·업무 규칙 | `backend/app/services/` |
| 테이블·컬럼·관계 | `backend/app/models/` |
| DB 구조 변경 이력 | `backend/migrations/versions/` |
| 로그인·예약 화면 | `frontend/src/pages/` |

각 화면의 `templates.ts`는 화면 마크업, `index.ts`는 이벤트와 화면 동작을 담당하도록 구성한다.

[구조 설명](docs/design/architecture.md) · [DB 대응표](docs/design/database.md)
