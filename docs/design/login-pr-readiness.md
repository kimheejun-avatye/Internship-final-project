# developer 머지와 로그인 이동 검증

- 작업: codex/login-only의 e087f49에 origin/developer ddb56f9 머지.
- 다른 teamproject1/codex/login, main, developer 원격에는 변경하지 않음.
- 회원가입 담당 코드·정책, users 부분 UNIQUE, 회의실·예약·캘린더 서비스와 DTO·모델·기존 migration을 보존.
- 팀 화면·CSS·임시 데이터를 포함하고 App 라우팅·ProtectedRoute·팀 AppLayout의 세션 로그아웃 및 비밀번호 변경 메뉴를 연결.
- 로그인 성공은 이전 목적지와 관계없이 /reservations, 기존 세션으로 인증 화면 접근도 /reservations로 이동.

## DB

기존 숫자 0003(팀 캘린더)과 login_0003(로그인)을 수정하지 않고 merge_0004로 연결했다. merge revision 자체는 데이터를 수정하지 않는다. 새 테스트 DB, login_0003에서 시작한 테스트 DB, 팀 0003에서 시작한 테스트 DB에서 단일 merge_0004 head로 적용됨을 확인했다. 양쪽 시작 DB의 기존 행·회원 인덱스가 보존됨을 검증했다. 기존 개발 DB는 수정하지 않았다.

## 검증

- 백엔드 85개 통과: 회원가입·로그인·비밀번호·세션·동시성·회의실·예약 조회.
- 프런트 26개 통과, TypeScript 검사·프로덕션 빌드 성공.
- 로그인 성공→예약하기, 기존 세션→예약하기, 비로그인 캘린더→로그인, 팀 메뉴·로그아웃 검증.
- 테스트 Origin은 로컬 .env의 5175 설정과 분리해 고정한다. 테스트 DB 이름도 TEST_DATABASE_URL에서 확정한다.
- 가입 담당 핵심 파일과 팀 조회 서비스·스키마는 최신 developer 원본과 비교한다.

## 범위

캘린더 화면은 기존 팀 mock 데이터를 유지한다. 서비스 구현을 보존했지만 캘린더 HTTP/API 연결 전체를 새로 구현하는 작업은 아니다. 관리자 기능 브랜치는 developer에 포함된 범위만 반영한다. 미래 변경의 병합 무충돌을 보장하지 않으며 PR 직전 갱신 상태를 다시 확인한다.
