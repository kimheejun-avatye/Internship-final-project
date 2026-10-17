import { FormEvent, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import Logo from "../../components/Logo";

export default function LoginPage() {
  const navigate = useNavigate();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  function submit(e: FormEvent) {
    e.preventDefault();
    // 로그인 API는 로그인 담당 작업에서 연결한다. 지금은 화면 이동만 한다
    navigate("/reservations");
  }

  return (
    <div className="auth-page">
      <form className="auth-box" onSubmit={submit}>
        <Logo className="auth-logo large" />
        <p className="auth-subtitle">회의실 예약 시스템</p>

        <div className="field">
          <label htmlFor="email">아이디</label>
          <div className="input-wrap">
            <input id="email" type="email" placeholder="회사 이메일" autoComplete="username" value={email} onChange={(e) => setEmail(e.target.value)} />
          </div>
        </div>
        <div className="field">
          <label htmlFor="password">비밀번호</label>
          <div className="input-wrap">
            <input id="password" type="password" placeholder="비밀번호" autoComplete="current-password" value={password} onChange={(e) => setPassword(e.target.value)} />
          </div>
        </div>

        <button type="submit" className="btn" style={{ width: "100%", marginTop: 20 }}>
          로그인
        </button>
        <div className="auth-links">
          <Link to="/signup" className="primary text-link">회원가입</Link>
          <span className="divider" />
          <button type="button" className="muted text-link" disabled>비밀번호 찾기</button>
        </div>
      </form>
    </div>
  );
}
