import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { MemoryRouter } from "react-router-dom";
import { afterEach, expect, it, vi } from "vitest";
import App from "./App";
import { AuthProvider } from "./auth/AuthProvider";
import { setCsrfToken } from "./shared/api/session-client";
const session = { user: { user_id: "u1", email: "member@example.com", name: "회원", team: "AVATYE", role: "MEMBER" }, csrf_token: "csrf", idle_expires_at: new Date(Date.now()+1800000).toISOString(), absolute_expires_at: new Date(Date.now()+28800000).toISOString() };
afterEach(() => { vi.unstubAllGlobals(); setCsrfToken(""); });
it("shows password management for the authenticated account without team feature navigation", async () => {
  vi.stubGlobal("fetch",vi.fn(async()=>new Response(JSON.stringify(session),{status:200})));
  render(<MemoryRouter initialEntries={["/profile"]}><AuthProvider><App /></AuthProvider></MemoryRouter>);
  expect(await screen.findByRole("heading",{level:1,name:"비밀번호 변경"})).toBeInTheDocument();
  expect(screen.queryByRole("link",{name:"예약하기"})).not.toBeInTheDocument();
  expect(screen.queryByRole("link",{name:"캘린더"})).not.toBeInTheDocument();
});
it("logs out through the server and returns to login", async () => {
  const fetch = vi.fn(async(path: string)=>path.endsWith("/logout") ? new Response(null,{status:204}) : new Response(JSON.stringify(session),{status:200}));
  vi.stubGlobal("fetch",fetch);
  render(<MemoryRouter initialEntries={["/profile"]}><AuthProvider><App /></AuthProvider></MemoryRouter>);
  await userEvent.click(await screen.findByRole("button",{name:"로그아웃"}));
  expect(await screen.findByRole("button",{name:"로그인"})).toBeInTheDocument();
  const call = (fetch.mock.calls as unknown as [string, RequestInit][]).find(([path])=>path.endsWith("/logout"));
  expect(call?.[1].method).toBe("POST");
  expect((call?.[1].headers as Record<string,string>)["X-CSRF-Token"]).toBe("csrf");
});
