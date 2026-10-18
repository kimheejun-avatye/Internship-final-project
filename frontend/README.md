# Frontend

React + TypeScript + Vite. 화면은 `src/pages/`, 공통 레이아웃은 `src/components/`, 스타일은 `src/styles/`에 있다.

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173, /api 요청은 http://127.0.0.1:8000 으로 프록시
npm run build    # 타입 검사 + 프로덕션 빌드
npm test         # 회원가입 화면 테스트 (vitest)
```

| 경로 | 화면 |
|---|---|
| `/login` | 로그인 |
| `/signup` | 회원가입 |
| `/reservations` | 회의실 예약 |
| `/calendar` | 예약 캘린더 |
| `/admin` | 관리자 |

서버 API가 연결되기 전까지 예약·구성원 데이터는 `src/mocks/data.ts`의 임시 데이터를 쓴다.

회원가입 화면은 백엔드 `/api/auth/signup/*`에 연결된다. 개발 서버와 함께 백엔드를 띄워야 한다
(`cd backend && SECRET_KEY=... .venv/bin/python -m uvicorn app.main:app`).
SMTP를 설정하지 않으면 인증번호가 백엔드 로그에 출력된다.
