# 실제 구현 구조

로그인 PR은 최신 developer의 팀 구조를 유지하고 인증을 추가한다.

| 위치 | 책임 |
|---|---|
| backend/app/api/routes | 팀 회원가입·회의실 HTTP API, 로그인·세션·비밀번호·프로필 HTTP API |
| backend/app/api/dependencies.py | 세션 인증·CSRF 검증 |
| backend/app/services | 업무 규칙. 예약·캘린더 서비스의 미구현 메서드는 팀 상태 그대로 유지 |
| backend/app/models | 회원·회의실·예약·참석자·알림 및 세션·로그인 제한·재설정 모델 |
| backend/app/schemas | 요청·응답 형식 |
| backend/app/core, db | 설정·보안 도구·DB 연결 |
| frontend/src/main.tsx | 실제 React 실행 시작 |
| frontend/src/App.tsx | 화면 경로와 레이아웃 연결 |
| frontend/src/auth | AuthProvider와 ProtectedRoute |
| frontend/src/layouts/AuthLayout.tsx | 로그인·회원가입·비밀번호 재설정 공통 틀 |
| frontend/src/components/AppLayout.tsx | 팀 공통 메뉴·본문 및 실제 서버 로그아웃 |
| frontend/src/pages | 팀 reservation/calendar/admin 화면과 인증·프로필 화면 |
| frontend/src/shared | 서버 통신·타입·공통 React hooks |
| frontend/src/mocks | 팀이 만든 임시 데이터, 로그인 PR에서 API로 교체하지 않음 |

폴더 트리는 컴포넌트 중첩 관계와 다르다. main.tsx의 AuthProvider가 App을 감싸고, App의 Route가 AuthLayout 또는 ProtectedRoute → 팀 AppLayout을 선택한다. 각 레이아웃의 Outlet에 실제 페이지가 표시된다.

초기 프런트의 빈 app/, main.ts, index.ts/templates.ts 뼈대는 developer에서 정리한 상태를 따른다. Python의 빈 __init__.py는 유지한다. 백엔드의 미구현 기능용 파일은 로그인 PR의 정리 대상으로 삭제하지 않는다.
