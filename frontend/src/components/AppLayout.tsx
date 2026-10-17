import { NavLink, Outlet, useNavigate } from "react-router-dom";

import Logo from "./Logo";

const MENU = [
  { to: "/reservations", label: "예약하기" },
  { to: "/calendar", label: "캘린더" },
  { to: "/admin", label: "관리자" },
];

export default function AppLayout() {
  const navigate = useNavigate();

  return (
    <div className="app">
      <header className="app-header">
        <Logo />
      </header>
      <div className="app-body">
        <aside className="sidebar">
          <nav>
            {MENU.map((item) => (
              <NavLink key={item.to} to={item.to} className={({ isActive }) => (isActive ? "active" : "")}>
                {item.label}
              </NavLink>
            ))}
          </nav>
          {/* 로그인/세션 처리는 로그인 담당 작업에서 연결한다 */}
          <button type="button" className="logout" onClick={() => navigate("/login")}>
            로그아웃
          </button>
        </aside>
        <main className="main">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
