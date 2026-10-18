import { FormEvent, useEffect, useState } from "react";
import { useAuth } from "../../auth/AuthProvider";
import { request } from "../../shared/api/client";
import PasswordChangeForm from "./PasswordChangeForm";
export default function ProfilePage() {
  const { session, reloadMe } = useAuth();
  const [name, setName] = useState(session?.user.name || ""); const [message, setMessage] = useState(""); const [error, setError] = useState(""); const [busy, setBusy] = useState(false);
  useEffect(() => { setName(session?.user.name || ""); }, [session?.user.name]);
  async function submit(e: FormEvent) { e.preventDefault(); if (busy) return; setBusy(true); setError(""); setMessage(""); try { await request("/api/users/me", "PATCH", { name }, true); await reloadMe(); setMessage("프로필을 저장했습니다."); } catch (e) { setError((e as Error).message); } finally { setBusy(false); } }
  return <><h1>내 프로필</h1><div className="profile-grid"><form className="profile-card card" onSubmit={submit}><h2>기본 정보</h2><p className="notice">{session?.user.email} · {session?.user.team}</p><div className="field"><label htmlFor="profile-name">이름</label><div className="input-wrap"><input id="profile-name" required maxLength={50} value={name} onChange={e => setName(e.target.value)} /></div></div>{error && <p role="alert" className="form-error">{error}</p>}{message && <p role="status" className="hint ok">{message}</p>}<button className="btn full-width" disabled={busy}>{busy ? "저장 중…" : "프로필 저장"}</button></form><PasswordChangeForm /></div></>;
}
