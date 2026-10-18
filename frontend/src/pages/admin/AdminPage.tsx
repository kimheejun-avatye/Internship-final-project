import { MEMBERS, RESERVATIONS, ROOMS } from "../../mocks/data";

export default function AdminPage() {
  const todayCount = RESERVATIONS.filter((r) => r.date === "2026-10-16").length;
  const active = ROOMS.filter((r) => r.status === "ACTIVE").length;
  const maintenance = ROOMS.length - active;
  const pending = MEMBERS.filter((m) => !m.approved).length;

  return (
    <>
      <h1 className="page-title">워크스페이스 관리</h1>

      <div className="stats">
        <div className="card stat">
          <div className="label">오늘의 예약</div>
          <div className="value">{todayCount}</div>
          <div className="sub">전체 회의실 기준</div>
        </div>
        <div className="card stat">
          <div className="label">사용 가능한 회의실</div>
          <div className="value">{active} / {ROOMS.length}</div>
          <div className="sub">{maintenance}개 회의실 점검 중</div>
        </div>
        <div className="card stat">
          <div className="label">전체 구성원</div>
          <div className="value">{MEMBERS.length}</div>
          <div className="sub">승인 대기 {pending}명</div>
        </div>
      </div>

      <section className="card panel">
        <h2>회의실 관리</h2>
        <table className="table">
          <thead>
            <tr><th>회의실</th><th>수용 인원</th><th>상태</th><th /></tr>
          </thead>
          <tbody>
            {ROOMS.map((r) => (
              <tr key={r.id}>
                <td className="strong">회의실 {r.letter}</td>
                <td>{r.capacity}명</td>
                <td>
                  {r.status === "ACTIVE" ? <span className="chip green">운영 중</span> : <span className="chip amber">점검 중</span>}
                </td>
                <td><button type="button" className="action">수정</button></td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      <section className="card panel">
        <h2>구성원 관리</h2>
        <table className="table">
          <thead>
            <tr><th>구성원</th><th>소속</th><th>역할</th><th>상태</th><th /></tr>
          </thead>
          <tbody>
            {MEMBERS.map((m) => (
              <tr key={m.id}>
                <td>
                  <div className="member">
                    <div className="avatar">{m.name[0]}</div>
                    <div>
                      <div className="name">{m.name}</div>
                      <div className="email">{m.email}</div>
                    </div>
                  </div>
                </td>
                <td>{m.team}</td>
                <td>{m.role}</td>
                <td>{m.approved ? <span className="chip green">승인됨</span> : <span className="chip amber">승인 대기</span>}</td>
                <td>
                  {m.approved ? (
                    <button type="button" className="action">수정</button>
                  ) : (
                    <>
                      <button type="button" className="action">승인</button>
                      <button type="button" className="action">거절</button>
                    </>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </>
  );
}
