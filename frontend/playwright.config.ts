// 画面の通しのテストの設定(Issue #38 の実装計画の T-8)。
// 一時の DB・API のサーバー・画面のサーバーは、globalSetup(e2e/support/global-setup.ts)で立てる。
// 結果は JUnit の junit-playwright.xml に出す(テストの手順の形)。
import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "e2e",
  testMatch: "**/*.spec.ts",
  globalSetup: "./e2e/support/global-setup.ts",
  // 一式は 1 つなので、テストは 1 つずつ流す
  workers: 1,
  fullyParallel: false,
  forbidOnly: true,
  retries: 0,
  reporter: [["list"], ["junit", { outputFile: "junit-playwright.xml" }]],
  use: {
    trace: "off",
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
