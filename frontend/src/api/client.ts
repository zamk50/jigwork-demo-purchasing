// API を呼ぶ役(方式設計の「API」。画面共通規則の「時間切れ」「メッセージの出し方」)。
// 型は backend の OpenAPI から生成した schema.d.ts を使う。
import type { components } from "./schema";

export type MeResponse = components["schemas"]["MeResponse"];
export type MenuResponse = components["schemas"]["MenuResponse"];
export type LoginRequest = components["schemas"]["LoginRequest"];

/** API を呼ぶ役。画面には props で渡し、テストでは決めた応答を返すものに差し替える。 */
export type FetchFn = (path: string, init?: RequestInit) => Promise<Response>;

/** 想定しない誤り(500 や通信の失敗)の文(画面共通規則の「メッセージの出し方」)。 */
export const UNEXPECTED_ERROR_MESSAGE = "時間をおいてもう一度試してください";

/** API の誤り。message は画面に出す文である。 */
export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/** ログインの API でない API の 401(ログインしていない・時間切れ)。画面はログイン画面に移る。 */
export class UnauthorizedError extends ApiError {
  constructor(message: string) {
    super(401, message);
    this.name = "UnauthorizedError";
  }
}

/**
 * 401 のときの動きを、後から差し替えられるように中継する。
 * 画面の移り方(React Router の navigate)は道が変わるたびに作り直されるが、API を呼ぶ役は作り直さないために使う。
 */
export class UnauthorizedRelay {
  private handler: () => void = () => undefined;

  setHandler(handler: () => void): void {
    this.handler = handler;
  }

  fire(): void {
    this.handler();
  }
}

export type Api = {
  /** ログインする。401 はログインの失敗で、ログイン画面に移らずに ApiError を投げる。 */
  login(body: LoginRequest): Promise<MeResponse>;
  logout(): Promise<void>;
  me(): Promise<MeResponse>;
  menu(): Promise<MenuResponse>;
};

const JSON_HEADERS = { "content-type": "application/json" };

async function readDetail(response: Response): Promise<string | null> {
  try {
    const body: unknown = await response.json();
    if (typeof body === "object" && body !== null && "detail" in body && typeof body.detail === "string") {
      return body.detail;
    }
  } catch {
    // 本文が JSON でなければ、文は無いものとする
  }
  return null;
}

/**
 * API を呼ぶ役を作る。
 * ログインの API を除く API で 401 が返ったら onUnauthorized を呼ぶ(画面はログイン画面に移る)。
 */
export function createApi(fetchFn: FetchFn, onUnauthorized: () => void): Api {
  async function send(path: string, init: RequestInit, isLogin: boolean): Promise<Response> {
    let response: Response;
    try {
      response = await fetchFn(path, { credentials: "same-origin", ...init });
    } catch {
      throw new ApiError(0, UNEXPECTED_ERROR_MESSAGE);
    }
    if (response.status === 401) {
      const detail = (await readDetail(response)) ?? UNEXPECTED_ERROR_MESSAGE;
      if (isLogin) {
        throw new ApiError(401, detail);
      }
      onUnauthorized();
      throw new UnauthorizedError(detail);
    }
    if (!response.ok) {
      throw new ApiError(response.status, UNEXPECTED_ERROR_MESSAGE);
    }
    return response;
  }

  async function sendJson<T>(path: string, init: RequestInit, isLogin = false): Promise<T> {
    const response = await send(path, init, isLogin);
    try {
      return (await response.json()) as T;
    } catch {
      throw new ApiError(response.status, UNEXPECTED_ERROR_MESSAGE);
    }
  }

  return {
    login: (body) =>
      sendJson<MeResponse>(
        "/api/auth/login",
        { method: "POST", headers: JSON_HEADERS, body: JSON.stringify(body) },
        true,
      ),
    // ログアウトの API は JSON だけを受けるので、空の JSON を付けて送る
    logout: async () => {
      await send("/api/auth/logout", { method: "POST", headers: JSON_HEADERS, body: "{}" }, false);
    },
    me: () => sendJson<MeResponse>("/api/me", { method: "GET" }),
    menu: () => sendJson<MenuResponse>("/api/menu", { method: "GET" }),
  };
}
