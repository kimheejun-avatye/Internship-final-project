import { useState } from "react";
import { Link, Outlet } from "react-router-dom";
import { useAuth } from "../auth/AuthProvider";
import Logo from "../components/Logo";
export default function AppLayout() {
  const { session, logout } = useAuth();
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState("");
  const exit = async () => { setBusy(true); setError(""); try { await logout(); } catch (e) { setError((e as Error).message); } finally { setBusy(false); } };
  return <div className="app-layout"><header className="account-header"><Link to="/profile"><Logo className="app-logo" /></Link><nav aria-label="내 계정"><Link to="/profile">비밀번호 변경</Link><span>{session?.user.name}님</span><button className="btn" disabled={busy} onClick={() => void exit()}>{busy ? "종료 중…" : "로그아웃"}</button></nav></header>{error && <p role="alert" className="form-error">{error}</p>}<main className="app-content"><Outlet /></main></div>;
}
