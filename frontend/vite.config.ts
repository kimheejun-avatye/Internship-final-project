import react from "@vitejs/plugin-react";
import { loadEnv } from "vite";
import { defineConfig } from "vitest/config";

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, ".", "");
  return {
    plugins: [react()],
    test: { environment: "jsdom", globals: true, setupFiles: "./src/test/setup.ts" },
    server: { proxy: { "/api": env.BACKEND_URL || "http://127.0.0.1:8000" } },
  };
});
