import { defineConfig, devices } from "@playwright/test";

const API = 8001;
const WEB = 3100;

export default defineConfig({
  testDir: "./e2e",
  timeout: 120_000,
  use: { baseURL: `http://localhost:${WEB}`, ...devices["Pixel 7"] },
  webServer: [
    {
      // mocked models: the smoke test never spends API credit
      command: `uv run uvicorn tests.e2e_app:app --port ${API}`,
      cwd: "../backend",
      url: `http://localhost:${API}/health`,
    },
    {
      command: `npx next dev -H 127.0.0.1 -p ${WEB}`,
      env: { API_ORIGIN: `http://localhost:${API}` },
      url: `http://localhost:${WEB}`,
    },
  ],
});
