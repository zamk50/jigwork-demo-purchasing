// #38/TC-15: 4 役割の利用者が画面でログインし、メニューの項目が項目表の行と一致する。
// 000002 は社員の項目の後に上長の項目が並ぶ(AC-1・AC-3。FR-001・FR-015〜FR-017)。
// 期待の値は、要件の正本 docs/requirements/functions/FNC-003.md の項目表(FR-016)から写す。
import { expect, test, type Page } from "@playwright/test";

import { seedPassword, webUrl } from "./support/env";

// 項目表(FR-016)の役割の行。役割の順(FR-017)に並べる
const EMPLOYEE = { role: "社員", items: ["品目の検索", "購入依頼の入力", "自分の依頼の一覧"] };
const MANAGER = { role: "上長", items: ["決裁待ちの一覧(自部署)"] };
const BUYER = {
  role: "購買担当",
  items: ["発注", "入荷の登録", "在庫の一覧", "品目の管理", "月次の集計", "会計への書き出し"],
};
const ADMIN = { role: "管理者", items: ["仕入先の管理", "区分の管理", "利用者と役割の管理"] };

type Row = { role: string; items: string[] };

const CASES: { employeeNo: string; rows: Row[] }[] = [
  { employeeNo: "000001", rows: [EMPLOYEE] },
  { employeeNo: "000002", rows: [EMPLOYEE, MANAGER] },
  { employeeNo: "000003", rows: [BUYER] },
  { employeeNo: "000004", rows: [ADMIN] },
];

async function login(page: Page, employeeNo: string): Promise<void> {
  await page.goto(webUrl("/login"));
  await page.getByLabel("社員番号").fill(employeeNo);
  await page.getByLabel("パスワード").fill(seedPassword(employeeNo));
  await page.getByRole("button", { name: "ログイン" }).click();
  await expect(page).toHaveURL(webUrl("/menu"));
  await expect(page.getByRole("heading", { level: 1, name: "メニュー" })).toBeVisible();
}

for (const { employeeNo, rows } of CASES) {
  test(`#38/TC-15 ${employeeNo} が画面でログインし、メニューの項目が項目表の${rows.map((r) => r.role).join("・")}の行と一致する`, async ({
    page,
  }) => {
    await login(page, employeeNo);

    // 役割の見出しが、項目表の役割の順に、持つ役割の分だけ並ぶ
    await expect(page.getByRole("heading", { level: 2 })).toHaveText(rows.map((r) => r.role));

    // 役割ごとのまとまりの中に、項目表のその行の項目だけが、行の順に並ぶ
    const sections = page.getByRole("region");
    await expect(sections).toHaveCount(rows.length);
    for (const [index, row] of rows.entries()) {
      const section = sections.nth(index);
      await expect(section.getByRole("heading", { level: 2 })).toHaveText(row.role);
      const items = section.getByRole("listitem");
      await expect(items).toHaveCount(row.items.length);
      await expect(items).toContainText(row.items);
    }
  });
}
