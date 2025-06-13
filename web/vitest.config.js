import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    environment: "happy-dom", // ou 'jsdom'
    globals: true, // Permite usar describe, it, expect sem importações
  },
});
