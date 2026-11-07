// #38/TC-16: 誤ったパスワードでは、ログイン画面のまま誤りの文が出る(AC-2。FR-002)。
// 誤りの文は、ログインの失敗の共通の文(FR-002-AC-01)である。画面はボタンの上に出す(画面共通規則)。
import { expect, test } from "@playwright/test";

import { seedPassword, webUrl } from "./support/env";

const LOGIN_FAILED_MESSAGE = "社員番号かパスワードが違います";

test("#38/TC-16 誤ったパスワードでは、ログイン画面のまま誤りの文が出る", async ({ page }) => {
  const employeeNo = "000001";
  await page.goto(webUrl("/login"));
  await page.getByLabel("社員番号").fill(employeeNo);
  // 初期データの正しいパスワードに文字を足して、必ず誤ったものにする
  await page.getByLabel("パスワード").fill(`${seedPassword(employeeNo)}x`);
  await page.getByRole("button", { name: "ログイン" }).click();

  await expect(page.getByRole("alert")).toHaveText(LOGIN_FAILED_MESSAGE);
  await expect(page).toHaveURL(webUrl("/login"));
  await expect(page.getByRole("heading", { level: 1, name: "ログイン" })).toBeVisible();
  await expect(page.getByRole("heading", { level: 1, name: "メニュー" })).toHaveCount(0);
});
