// 画面の部品のテストの道具。API のサーバーの代わりに、決めた応答を返す fetch を作る。
// 画面には fetch を props で渡す(モジュールの差し替えは使わない)。
// jest-dom の照合(toBeDisabled など)も、ここで vitest の expect に足す。
/// <reference types="@testing-library/jest-dom/vitest" />
import * as matchers from "@testing-library/jest-dom/matchers";
import { render } from "@testing-library/react";
import { MemoryRouter, useLocation } from "react-router-dom";
import { expect } from "vitest";

import type { FetchFn } from "@/api/client";
import type { components } from "@/api/schema";
import { AppRoutes } from "@/AppRoutes";

expect.extend(matchers);

export type MeResponse = components["schemas"]["MeResponse"];
export type MenuResponse = components["schemas"]["MenuResponse"];

/** 画面が API を呼んだ記録 1 つ。 */
export type ApiCall = {
  method: string;
  path: string;
  body: string | null;
  contentType: string | null;
};

/** 応答を作る役。「POST /api/auth/login」のような、方法と道の組ごとに置く。 */
export type Handler = () => Response | Promise<Response>;

/** JSON の応答を作る。 */
export function jsonResponse(status: number, body: unknown): Response {
  return new Response(JSON.stringify(body), {
    status,
    headers: { "content-type": "application/json" },
  });
}

/** 本文のない応答(204 など)を作る。 */
export function emptyResponse(status: number): Response {
  return new Response(null, { status });
}

/** 決めた応答を返す fetch と、呼ばれた記録を作る。決めていない組には 404 を返す。 */
export function createFakeFetch(handlers: Record<string, Handler>): {
  fetchFn: FetchFn;
  calls: ApiCall[];
} {
  const calls: ApiCall[] = [];
  const fetchFn: FetchFn = async (path, init) => {
    const method = (init?.method ?? "GET").toUpperCase();
    const headers = new Headers(init?.headers);
    calls.push({
      method,
      path,
      body: typeof init?.body === "string" ? init.body : null,
      contentType: headers.get("content-type"),
    });
    const handler = handlers[`${method} ${path}`];
    if (handler === undefined) {
      return jsonResponse(404, { detail: "Not Found" });
    }
    return handler();
  };
  return { fetchFn, calls };
}

/** 今の画面の道を出す。テストで画面が移ったかを確かめるために置く。 */
function LocationProbe() {
  const location = useLocation();
  return <output data-testid="location">{location.pathname}</output>;
}

/** 道 path から、画面全体を描く。 */
export function renderApp(path: string, fetchFn: FetchFn) {
  return render(
    <MemoryRouter initialEntries={[path]}>
      <AppRoutes fetchFn={fetchFn} />
      <LocationProbe />
    </MemoryRouter>,
  );
}

/** 応答を後から決められる約束を作る。送信中の画面を確かめるために使う。 */
export function deferred<T>(): { promise: Promise<T>; resolve: (value: T) => void } {
  const holder: { resolve?: (value: T) => void } = {};
  const promise = new Promise<T>((done) => {
    holder.resolve = done;
  });
  return { promise, resolve: (value) => holder.resolve?.(value) };
}
