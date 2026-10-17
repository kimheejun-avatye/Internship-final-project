import { FormEvent, useState } from "react";
import { Link } from "react-router-dom";

import Logo from "../../components/Logo";

type Team = "AVATYE" | "GURU";

export default function SignupPage() {
  const [team, setTeam] = useState<Team>("AVATYE");
  const [agreed, setAgreed] = useState(false);

  function submit(e: FormEvent) {
    e.preventDefault();
  }

  return (
    <div className="auth-page">
      <form className="auth-box signup" onSubmit={submit}>
        <Logo className="auth-logo small" />

        <div className="field">
          <label htmlFor="name">이름</label>
          <div className="input-wrap"><input id="name" placeholder="이름" /></div>
        </div>

        <div className="field">
          <label htmlFor="email">아이디</label>
          <div className="input-wrap">
            <input id="email" type="email" placeholder="회사 이메일" />
            <button type="button" className="inline-btn">인증번호 요청</button>
          </div>
        </div>

        <div className="field">
          <label htmlFor="code">이메일 인증</label>
          <div className="input-wrap">
            <input id="code" inputMode="numeric" maxLength={6} placeholder="인증번호 6자리" />
            <button type="button" className="inline-btn">인증 확인</button>
          </div>
          <p className="hint">회사 이메일로 받은 인증번호를 입력해 주세요.</p>
        </div>

        <div className="field">
          <label htmlFor="password">비밀번호</label>
          <div className="input-wrap"><input id="password" type="password" placeholder="비밀번호" autoComplete="new-password" /></div>
        </div>

        <div className="field">
          <label htmlFor="password2">비밀번호 확인</label>
          <div className="input-wrap"><input id="password2" type="password" placeholder="비밀번호 확인" autoComplete="new-password" /></div>
        </div>

        <div className="field">
          <span className="field-label">소속</span>
          <div className="team-options" role="radiogroup" aria-label="소속">
            {(["AVATYE", "GURU"] as Team[]).map((t) => (
              <button key={t} type="button" role="radio" aria-checked={team === t} className={`team-option${team === t ? " selected" : ""}`} onClick={() => setTeam(t)}>
                <span className="dot" />
                {t}
              </button>
            ))}
          </div>
        </div>

        <label className="consent">
          <input type="checkbox" checked={agreed} onChange={(e) => setAgreed(e.target.checked)} />
          [필수] 개인정보 수집·이용 동의
          <button type="button" className="view">보기</button>
        </label>

        <button type="submit" className="btn" style={{ width: "100%", height: 52 }}>회원가입</button>
        <Link to="/login" className="back-link">로그인으로 돌아가기</Link>
      </form>
    </div>
  );
}
