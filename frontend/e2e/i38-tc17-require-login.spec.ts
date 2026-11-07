// #38/TC-17: ログインせずにメニューの画面を開くとログイン画面に移る。ログアウトの後も同じである
// (AC-4・AC-5。FR-007・FR-012・FR-013)。
import { expect, test } from "@playwright/test";

import { seedPassword, webUrl } from "./support/env";

test("#38/TC-17 ログインせずにメニューの画面を開くとログイン画面に移る", async ({ page }) => {
  await page.goto(webUrl("/menu"));

  await expect(page).toHaveURL(webUrl("/login"));
  await expect(page.getByRole("heading", { level: 1, name: "ログイン" })).toBeVisible();
});

test("#38/TC-17 ログアウトするとログイン画面に移り、その後にメニューの画面を開いてもログイン画面に移る", async ({
  page,
}) => {
  const employeeNo = "000002";
  await page.goto(webUrl("/login"));
  await page.getByLabel("社員番号").fill(employeeNo);
  await page.getByLabel("パスワード").fill(seedPassword(employeeNo));
  await page.getByRole("button", { name: "ログイン" }).click();
  await expect(page).toHaveURL(webUrl("/menu"));
  await expect(page.getByRole("heading", { level: 1, name: "メニュー" })).toBeVisible();

  // メニューの画面でログアウトすると、ログイン画面に移る(FR-012-AC-01)
  await page.getByRole("button", { name: "ログアウト" }).click();
  await expect(page).toHaveURL(webUrl("/login"));
  await expect(page.getByRole("heading", { level: 1, name: "ログイン" })).toBeVisible();

  // ログアウトの後にメニューの画面を開くと、ログイン画面に移る(FR-013-AC-01)
  await page.goto(webUrl("/menu"));
  await expect(page).toHaveURL(webUrl("/login"));
  await expect(page.getByRole("heading", { level: 1, name: "ログイン" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 1, name: "メニュー" })).toHaveCount(0);
});
