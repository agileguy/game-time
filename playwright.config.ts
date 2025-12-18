import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration for E2E tests.
 *
 * See https://playwright.dev/docs/test-configuration
 */
export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  // Run tests with 2 workers for faster execution
  workers: 2,
  reporter: 'html',

  use: {
    baseURL: 'http://localhost:7000',
    trace: 'on-first-retry',
  },

  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    // Disabled: Firefox and WebKit browsers not installed
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },
    // Mobile viewports disabled for now
    // {
    //   name: 'Mobile Chrome',
    //   use: { ...devices['Pixel 5'] },
    // },
    // {
    //   name: 'Mobile Safari',
    //   use: { ...devices['iPhone 12'] },
    // },
  ],

  webServer: {
    command: process.env.CI
      ? 'cd backend && TESTING=true uvicorn app.main:app --host 0.0.0.0 --port 7000'
      : 'cd backend && TESTING=true .venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 7000',
    url: 'http://localhost:7000/health/ready',
    reuseExistingServer: true,  // Always reuse - CI workflow starts servers manually
    timeout: 120 * 1000,
  },
});
