// #38/TC-23: ログインのボタンを押してからメニューの項目が出るまでを 3 回測り、中央値が 1 秒以内である(NFR-001)。
// 1 回ごとに新しいブラウザの文脈(クッキーの無い状態)で測る。測った値はテストの annotation に残す。
import { expect, test } from "@playwright/test";

import { seedPassword, webUrl } from "./support/env";

const RUNS = 3;
const LIMIT_MS = 1000;

/** 3 回の値の中央値。最も小さい値と最も大きい値を除いた残りである。 */
function medianOfThree(values: number[]): number {
  if (values.length !== 3) {
    throw new Error(`測った値は 3 つのはずが ${values.length} つある`);
  }
  const total = values.reduce((sum, value) => sum + value, 0);
  return total - Math.min(...values) - Math.max(...values);
}

test("#38/TC-23 ログインのボタンを押してからメニューの項目が出るまでの 3 回の中央値が 1 秒以内である", async ({
  browser,
}) => {
  const employeeNo = "000001";
  const durations: number[] = [];
  for (let run = 0; run < RUNS; run += 1) {
    const context = await browser.newContext();
    try {
      const page = await context.newPage();
      await page.goto(webUrl("/login"));
      await page.getByLabel("社員番号").fill(employeeNo);
      await page.getByLabel("パスワード").fill(seedPassword(employeeNo));
      const button = page.getByRole("button", { name: "ログイン" });
      await expect(button).toBeEnabled();

      const started = performance.now();
      await button.click();
      // メニューの項目(社員の行の最初の項目)が出るまで
      await expect(page.getByRole("listitem").first()).toBeVisible();
      durations.push(Math.round(performance.now() - started));
      await expect(page).toHaveURL(webUrl("/menu"));
    } finally {
      await context.close();
    }
  }

  const result = medianOfThree(durations);
  test.info().annotations.push({
    type: "NFR-001 ログインからメニューの項目まで(ミリ秒)",
    description: `測った値 ${durations.join(", ")} / 中央値 ${result} / 目標 ${LIMIT_MS} 以内`,
  });
  console.log(`#38/TC-23 測った値(ミリ秒): ${durations.join(", ")} 中央値: ${result}`);
  expect(result, `測った値 ${durations.join(", ")} ミリ秒の中央値 ${result} が ${LIMIT_MS} を超える`).toBeLessThanOrEqual(
    LIMIT_MS,
  );
});
