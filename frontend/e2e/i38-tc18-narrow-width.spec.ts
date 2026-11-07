// #38/TC-18: 幅 375px で、ログイン画面とメニューの画面が横にはみ出さない(AC-1。FR-011・NFR-010)。
// はみ出しは、文書の横の広さ(scrollWidth)が画面の幅(clientWidth)を超えるかで見る。
// メニューは項目のいちばん多い購買担当(000003)で見る。
import { expect, test, type Page } from "@playwright/test";

import { seedPassword, webUrl } from "./support/env";

const NARROW_WIDTH = 375;

test.use({ viewport: { width: NARROW_WIDTH, height: 667 } });

async function horizontalOverflow(page: Page): Promise<{ scrollWidth: number; clientWidth: number }> {
  return page.evaluate(() => ({
    scrollWidth: document.documentElement.scrollWidth,
    clientWidth: document.documentElement.clientWidth,
  }));
}

async function expectNoOverflow(page: Page): Promise<void> {
  const { scrollWidth, clientWidth } = await horizontalOverflow(page);
  expect(clientWidth).toBe(NARROW_WIDTH);
  expect(scrollWidth, `横の広さ ${scrollWidth}px が画面の幅 ${clientWidth}px を超える`).toBeLessThanOrEqual(
    clientWidth,
  );
}

test("#38/TC-18 幅 375px で、ログイン画面とメニューの画面が横にはみ出さない", async ({ page }) => {
  const employeeNo = "000003";
  await page.goto(webUrl("/login"));
  await expect(page.getByRole("button", { name: "ログイン" })).toBeVisible();
  await expectNoOverflow(page);

  await page.getByLabel("社員番号").fill(employeeNo);
  await page.getByLabel("パスワード").fill(seedPassword(employeeNo));
  await page.getByRole("button", { name: "ログイン" }).click();
  await expect(page).toHaveURL(webUrl("/menu"));
  await expect(page.getByRole("heading", { level: 2, name: "購買担当" })).toBeVisible();
  await expect(page.getByRole("listitem")).toHaveCount(6);
  await expectNoOverflow(page);

  // 横にはみ出さずに操作できる: ログアウトのボタンが画面の幅の内にあり、押せる
  const logout = page.getByRole("button", { name: "ログアウト" });
  const box = await logout.boundingBox();
  expect(box).not.toBeNull();
  if (box !== null) {
    expect(box.x).toBeGreaterThanOrEqual(0);
    expect(box.x + box.width).toBeLessThanOrEqual(NARROW_WIDTH);
  }
  await logout.click();
  await expect(page).toHaveURL(webUrl("/login"));
});
