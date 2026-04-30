/**
 * Playwright 설정 — FlowBiz_ultra E2E
 *
 * 문서번호: FBU-PLAN-UI-V2-STANDALONE-IMPL-v7 §11.6.2
 * 작성자:   [claude]
 * 출처:     [claude]flowbiz_ui_v2_standalone_design_implementation_plan_v7_20260430.md
 *
 * 핵심:
 *  - baseURL: 127.0.0.1:8012 고정 (run_e2e.sh가 기동하는 test 서버)
 *  - workers: 1 (FastAPI 단일 인스턴스 + snapshot 충돌 방지)
 *  - chromium 단일 (Phase 0 진입 시 `npm run test:install` 필요)
 *  - run_e2e.sh가 외부에서 uvicorn 기동 → Playwright의 webServer 미사용
 */
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  timeout: 30_000,
  expect: { timeout: 5_000 },

  fullyParallel: false,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  workers: 1,

  reporter: [
    ['html', { outputFolder: 'playwright-report', open: 'never' }],
    ['list']
  ],

  use: {
    baseURL: 'http://127.0.0.1:8012',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    actionTimeout: 10_000,
    navigationTimeout: 15_000,
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],

  // run_e2e.sh가 uvicorn을 외부에서 기동 — webServer 미사용
});
