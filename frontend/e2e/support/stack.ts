// 画面の通しのテストの起動の役(Issue #38 の実装計画の T-8)。
//
// 1. 一時ディレクトリに PostgreSQL 18 を立てる。常駐のサービスは使わず、unix ソケットだけで待ち受ける
//    (backend/tests/conftest.py の postgres_server と同じ作り)。
// 2. 移行(alembic upgrade head)と初期データのコマンド(python -m app.seed)を流す。
//    初期データのパスワードは、そのたびに作る乱数にする。
// 3. API のサーバー(uvicorn app.main:create_app --factory)と画面のサーバー(vite)を、空いている口で立てる。
//
// Python のコマンドは作業のディレクトリを一時のものにし、環境変数をここで決めたものだけにする
// (手元の backend/.env を読ませないため)。
import { spawn, type ChildProcess } from "node:child_process";
import { randomBytes } from "node:crypto";
import { existsSync, mkdirSync, mkdtempSync, readFileSync, rmSync } from "node:fs";
import { createServer as createNetServer } from "node:net";
import { tmpdir } from "node:os";
import { join, resolve } from "node:path";

import { createServer as createViteServer, type ViteDevServer } from "vite";

const FRONTEND = resolve(import.meta.dirname, "..", "..");
const BACKEND = resolve(FRONTEND, "..", "backend");
const PYTHON = join(BACKEND, ".venv", "bin", "python");
const PG_BIN = "/usr/lib/postgresql/18/bin";
const PG_USER = "postgres";
const PG_PORT = 5432;
const HOST = "127.0.0.1";

// 社員番号ごとのパスワードの環境変数(方式設計の「初期データ」の節)
const PASSWORD_VARIABLE_BY_EMPLOYEE_NO: Readonly<Record<string, string>> = {
  "000001": "SEED_PASSWORD_EMPLOYEE",
  "000002": "SEED_PASSWORD_MANAGER",
  "000003": "SEED_PASSWORD_BUYER",
  "000004": "SEED_PASSWORD_ADMIN",
};

/** 立てた一式。passwords は社員番号 → 初期データのパスワード。stop で止めて消す。 */
export type Stack = {
  webUrl: string;
  apiUrl: string;
  passwords: Record<string, string>;
  stop: () => Promise<void>;
};

type RunResult = { code: number | null; output: string };

function run(command: string, args: string[], options: { cwd: string; env?: NodeJS.ProcessEnv }): Promise<RunResult> {
  return new Promise((resolvePromise, reject) => {
    const child = spawn(command, args, { cwd: options.cwd, env: options.env ?? process.env, stdio: "pipe" });
    let output = "";
    child.stdout.on("data", (chunk: Buffer) => (output += chunk.toString()));
    child.stderr.on("data", (chunk: Buffer) => (output += chunk.toString()));
    child.on("error", reject);
    child.on("close", (code) => resolvePromise({ code, output }));
  });
}

async function mustRun(
  label: string,
  command: string,
  args: string[],
  options: { cwd: string; env?: NodeJS.ProcessEnv },
): Promise<void> {
  const result = await run(command, args, options);
  if (result.code !== 0) {
    throw new Error(`${label}が失敗した(終了コード ${String(result.code)}):\n${result.output}`);
  }
}

/** 空いている TCP の口を 1 つ選ぶ。 */
function freePort(): Promise<number> {
  return new Promise((resolvePromise, reject) => {
    const server = createNetServer();
    server.on("error", reject);
    server.listen(0, HOST, () => {
      const address = server.address();
      if (address === null || typeof address === "string") {
        server.close();
        reject(new Error("空いている口を選べなかった"));
        return;
      }
      server.close(() => resolvePromise(address.port));
    });
  });
}

function randomSecret(bytes: number): string {
  return randomBytes(bytes).toString("base64url");
}

/** Python のコマンドに渡す環境変数。PATH のほかは、ここで決めたものだけにする。 */
function pythonEnv(variables: Record<string, string>): NodeJS.ProcessEnv {
  return { PATH: process.env.PATH ?? "", PYTHONPATH: BACKEND, ...variables };
}

/** url に HTTP で応えるまで待つ。応えの状態は問わない(ログインの要る API は 401 で応える)。 */
async function waitForHttp(url: string, label: string, child: ChildProcess, log: () => string): Promise<void> {
  const deadline = Date.now() + 60_000;
  while (Date.now() < deadline) {
    if (child.exitCode !== null) {
      throw new Error(`${label}が起動の途中で止まった(終了コード ${String(child.exitCode)}):\n${log()}`);
    }
    try {
      await fetch(url);
      return;
    } catch {
      await new Promise((r) => setTimeout(r, 200));
    }
  }
  throw new Error(`${label}が 60 秒のうちに応えなかった:\n${log()}`);
}

function stopProcess(child: ChildProcess): Promise<void> {
  if (child.exitCode !== null || child.signalCode !== null) return Promise.resolve();
  return new Promise((resolvePromise) => {
    child.once("exit", () => resolvePromise());
    child.kill("SIGTERM");
    setTimeout(() => child.kill("SIGKILL"), 10_000).unref();
  });
}

/** 一時の DB・API のサーバー・画面のサーバーを立てる。途中で失敗すれば、立てた分を止めて消してから投げる。 */
export async function startStack(): Promise<Stack> {
  const base = mkdtempSync(join(tmpdir(), "e2e-"));
  const data = join(base, "data");
  const work = join(base, "work");
  const cleanups: (() => Promise<void>)[] = [];
  const stop = async () => {
    // 立てた順の逆に止める
    for (let cleanup = cleanups.pop(); cleanup !== undefined; cleanup = cleanups.pop()) {
      try {
        await cleanup();
      } catch {
        // 止める途中の失敗は、残りを止めるのを妨げない
      }
    }
    rmSync(base, { recursive: true, force: true });
  };

  try {
    // 1. 一時の PostgreSQL
    await mustRun(
      "initdb",
      join(PG_BIN, "initdb"),
      ["-D", data, "-U", PG_USER, "-A", "trust", "-E", "UTF8", "--no-locale", "--no-sync"],
      { cwd: base },
    );
    const pgLog = join(base, "server.log");
    const pgOptions = `-c listen_addresses='' -k ${base} -p ${String(PG_PORT)} -c fsync=off`;
    try {
      await mustRun("PostgreSQL の起動", join(PG_BIN, "pg_ctl"), ["-D", data, "-l", pgLog, "-o", pgOptions, "-w", "start"], {
        cwd: base,
      });
    } catch (error) {
      const log = existsSync(pgLog) ? readFileSync(pgLog, "utf8") : "";
      throw new Error(`${error instanceof Error ? error.message : String(error)}\nサーバーのログ:\n${log}`, { cause: error });
    }
    cleanups.push(async () => {
      await run(join(PG_BIN, "pg_ctl"), ["-D", data, "-m", "immediate", "-w", "stop"], { cwd: base });
    });
    const databaseUrl = `postgresql+psycopg://${PG_USER}@/postgres?host=${base}&port=${String(PG_PORT)}`;

    // 2. 移行と初期データ。作業のディレクトリは一時のもの(backend/.env を読ませない)
    mkdirSync(work);
    await mustRun("移行", PYTHON, ["-m", "alembic", "-c", join(BACKEND, "alembic.ini"), "upgrade", "head"], {
      cwd: work,
      env: pythonEnv({ DATABASE_URL: databaseUrl }),
    });
    const passwords: Record<string, string> = {};
    const seedVariables: Record<string, string> = {};
    for (const [employeeNo, variable] of Object.entries(PASSWORD_VARIABLE_BY_EMPLOYEE_NO)) {
      const password = randomSecret(16);
      passwords[employeeNo] = password;
      seedVariables[variable] = password;
    }
    await mustRun("初期データのコマンド", PYTHON, ["-m", "app.seed"], {
      cwd: work,
      env: pythonEnv({ DATABASE_URL: databaseUrl, ...seedVariables }),
    });

    // 3. API のサーバー。画面は http で配るので、クッキーに Secure を付けない
    const apiPort = await freePort();
    const apiUrl = `http://${HOST}:${String(apiPort)}`;
    const api = spawn(
      PYTHON,
      ["-m", "uvicorn", "app.main:create_app", "--factory", "--host", HOST, "--port", String(apiPort)],
      {
        cwd: work,
        env: pythonEnv({ DATABASE_URL: databaseUrl, SESSION_SECRET: randomSecret(32), COOKIE_SECURE: "false" }),
        stdio: "pipe",
      },
    );
    let apiLog = "";
    api.stdout.on("data", (chunk: Buffer) => (apiLog += chunk.toString()));
    api.stderr.on("data", (chunk: Buffer) => (apiLog += chunk.toString()));
    cleanups.push(() => stopProcess(api));
    await waitForHttp(`${apiUrl}/api/menu`, "API のサーバー", api, () => apiLog);

    // 4. 画面のサーバー。/api を、立てた API のサーバーへ中継する
    const webPort = await freePort();
    const vite: ViteDevServer = await createViteServer({
      root: FRONTEND,
      configFile: join(FRONTEND, "vite.config.ts"),
      logLevel: "warn",
      server: { host: HOST, port: webPort, strictPort: true, proxy: { "/api": apiUrl } },
    });
    cleanups.push(() => vite.close());
    await vite.listen();
    const webUrl = `http://${HOST}:${String(webPort)}`;

    return { webUrl, apiUrl, passwords, stop };
  } catch (error) {
    await stop();
    throw error;
  }
}
