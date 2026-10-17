# Frontend

React + TypeScript + Vite. 화면은 `src/pages/`, 공통 레이아웃은 `src/components/`, 스타일은 `src/styles/`에 있다.

```bash
cd frontend
npm install
npm run dev      # http://localhost:5173, /api 요청은 http://127.0.0.1:8000 으로 프록시
npm run build    # 타입 검사 + 프로덕션 빌드
```

| 경로 | 화면 |
|---|---|
| `/login` | 로그인 |
| `/signup` | 회원가입 |
| `/reservations` | 회의실 예약 |
| `/calendar` | 예약 캘린더 |
| `/admin` | 관리자 |

서버 API가 연결되기 전까지 예약·구성원 데이터는 `src/mocks/data.ts`의 임시 데이터를 쓴다.
