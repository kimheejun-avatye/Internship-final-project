import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  test: { environment: "jsdom", globals: true, setupFiles: "./src/test/setup.ts" },
  server: {
    // 개발 중에는 /api 요청을 FastAPI(uvicorn 기본 포트)로 넘긴다
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
});
