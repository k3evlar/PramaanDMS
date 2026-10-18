/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development, /api is proxied to a local API on port 8000 (the Docker stack uses nginx instead).
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": { target: "http://127.0.0.1:8000", rewrite: (path) => path.replace(/^\/api/, "") },
    },
  },
  build: { sourcemap: false },
  test: { environment: "jsdom" },
});
