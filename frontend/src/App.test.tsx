import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";
import App from "./App";
import { AuthProvider } from "./auth/AuthProvider";
import { setCsrfToken } from "./shared/api/session-client";
const session = { user: { user_id: "u1", email: "member@example.com", name: "회원", team: "AVATYE", role: "MEMBER" }, csrf_token: "csrf", idle_expires_at: new Date(Date.now()+1800000).toISOString(), absolute_expires_at: new Date(Date.now()+28800000).toISOString() };
afterEach(() => { vi.unstubAllGlobals(); setCsrfToken(""); });
it("restores login and keeps the team's calendar and reservation navigation", async () => {
  vi.stubGlobal("fetch",vi.fn(async()=>new Response(JSON.stringify(session),{status:200})));
  render(<MemoryRouter initialEntries={["/calendar"]}><AuthProvider><App /></AuthProvider></MemoryRouter>);
  expect(await screen.findByRole("heading",{name:"예약 캘린더"})).toBeInTheDocument();
  expect(screen.getByRole("link",{name:"예약하기"})).toHaveAttribute("href","/reservations");
  expect(screen.getByRole("link",{name:"관리자"})).toHaveAttribute("href","/admin");
});
it("uses server logout from the login-owned account layout", async () => {
  const fetch = vi.fn(async(path: string)=>path.endsWith("/logout") ? new Response(null,{status:204}) : new Response(JSON.stringify(session),{status:200}));
  vi.stubGlobal("fetch",fetch);
  render(<MemoryRouter initialEntries={["/profile"]}><AuthProvider><App /></AuthProvider></MemoryRouter>);
  await userEvent.click(await screen.findByRole("button",{name:"로그아웃"}));
  expect(await screen.findByRole("button",{name:"로그인"})).toBeInTheDocument();
  const call = (fetch.mock.calls as unknown as [string, RequestInit][]).find(([path])=>path.endsWith("/logout"));
  expect(call?.[1].method).toBe("POST");
  expect((call?.[1].headers as Record<string,string>)["X-CSRF-Token"]).toBe("csrf");
});
