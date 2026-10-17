import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    // 개발 중에는 /api 요청을 FastAPI(uvicorn 기본 포트)로 넘긴다
    proxy: { "/api": "http://127.0.0.1:8000" },
  },
});
