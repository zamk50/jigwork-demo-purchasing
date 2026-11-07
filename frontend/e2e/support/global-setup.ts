// 通しのテストの全体の前に一式を立て、終われば止めて消す(Playwright の globalSetup)。
// 画面の配信元と初期データのパスワードは、環境変数でテストの側に渡す(e2e/support/env.ts で読む)。
import { E2E_PASSWORDS, E2E_WEB_URL } from "./env";
import { startStack } from "./stack";

export default async function globalSetup(): Promise<() => Promise<void>> {
  const stack = await startStack();
  process.env[E2E_WEB_URL] = stack.webUrl;
  process.env[E2E_PASSWORDS] = JSON.stringify(stack.passwords);
  return stack.stop;
}
