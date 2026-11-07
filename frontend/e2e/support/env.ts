// 起動の役(e2e/support/stack.ts)が立てた一式の在りかを、テストの側で読む役。
export const E2E_WEB_URL = "E2E_WEB_URL";
export const E2E_PASSWORDS = "E2E_PASSWORDS";

function required(name: string): string {
  const value = process.env[name];
  if (value === undefined || value === "") {
    throw new Error(`環境変数 ${name} が無い。通しのテストは playwright.config.ts の globalSetup から流す`);
  }
  return value;
}

/** 画面の配信元(例 http://127.0.0.1:5173)に path を付けた URL。 */
export function webUrl(path: string): string {
  return new URL(path, required(E2E_WEB_URL)).toString();
}

/** 初期データの利用者のパスワード。起動のたびに作る乱数である。 */
export function seedPassword(employeeNo: string): string {
  const passwords = JSON.parse(required(E2E_PASSWORDS)) as Record<string, string>;
  const password = passwords[employeeNo];
  if (password === undefined) {
    throw new Error(`社員番号 ${employeeNo} は初期データに無い`);
  }
  return password;
}
