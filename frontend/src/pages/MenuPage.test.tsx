// @vitest-environment jsdom
// #38/TC-14: メニューの画面が役割ごとに項目を並べ、準備中の項目を押せない。
// ログインの API でない API の 401(時間切れを含む)でログイン画面に移る。
import { cleanup, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test } from "vitest";

import {
  createFakeFetch,
  emptyResponse,
  jsonResponse,
  renderApp,
  type MeResponse,
  type MenuResponse,
} from "@/testing/fakeApi";

afterEach(cleanup);

const LOGIN_REQUIRED = { detail: "ログインしてください" };

const ME: MeResponse = {
  employee_no: "000002",
  name: "上長 二郎",
  department: "営業部",
  roles: [
    { code: "employee", name: "社員" },
    { code: "manager", name: "上長" },
  ],
};

const MENU: MenuResponse = {
  groups: [
    {
      role: { code: "employee", name: "社員" },
      items: [
        { code: "item_search", name: "品目の検索", available: false },
        { code: "purchase_request_entry", name: "購入依頼の入力", available: false },
        { code: "my_requests", name: "自分の依頼の一覧", available: false },
      ],
    },
    {
      role: { code: "manager", name: "上長" },
      items: [{ code: "approval_queue", name: "決裁待ちの一覧(自部署)", available: false }],
    },
  ],
};

/** 見える名前に text を含むかで要素を選ぶ。 */
function nameIncludes(text: string) {
  return (name: string) => name.includes(text);
}

function location() {
  return screen.getByTestId("location");
}

test("#38/TC-14 メニューの画面は、役割の見出しごとに項目を API の順に並べる", async () => {
  const { fetchFn } = createFakeFetch({
    "GET /api/me": () => jsonResponse(200, ME),
    "GET /api/menu": () => jsonResponse(200, MENU),
  });
  renderApp("/menu", fetchFn);

  const headings = await screen.findAllByRole("heading", { level: 2 });
  expect(headings.map((heading) => heading.textContent)).toEqual(["社員", "上長"]);

  const employee = screen.getByRole("region", { name: "社員" });
  expect(within(employee).getAllByRole("button").map((button) => button.textContent)).toEqual([
    expect.stringContaining("品目の検索"),
    expect.stringContaining("購入依頼の入力"),
    expect.stringContaining("自分の依頼の一覧"),
  ]);
  const manager = screen.getByRole("region", { name: "上長" });
  expect(within(manager).getAllByRole("button").map((button) => button.textContent)).toEqual([
    expect.stringContaining("決裁待ちの一覧(自部署)"),
  ]);
});

test("#38/TC-14 メニューの画面の上に、氏名と部署とログアウトのボタンを出す", async () => {
  const { fetchFn } = createFakeFetch({
    "GET /api/me": () => jsonResponse(200, ME),
    "GET /api/menu": () => jsonResponse(200, MENU),
  });
  renderApp("/menu", fetchFn);

  expect(await screen.findByText("上長 二郎")).toBeInTheDocument();
  expect(screen.getByText("営業部")).toBeInTheDocument();
  expect(screen.getByRole("button", { name: "ログアウト" })).toBeEnabled();
});

test("#38/TC-14 準備中の項目は「準備中」を添えて押せず、押しても画面は移らない", async () => {
  const user = userEvent.setup();
  const { fetchFn } = createFakeFetch({
    "GET /api/me": () => jsonResponse(200, ME),
    "GET /api/menu": () => jsonResponse(200, MENU),
  });
  renderApp("/menu", fetchFn);

  const item = await screen.findByRole("button", { name: nameIncludes("品目の検索") });
  expect(item).toBeDisabled();
  expect(item).toHaveTextContent("準備中");
  for (const group of MENU.groups) {
    for (const menuItem of group.items) {
      const button = screen.getByRole("button", { name: nameIncludes(menuItem.name) });
      expect(button).toBeDisabled();
      expect(button).toHaveTextContent("準備中");
    }
  }

  await user.click(item);
  expect(location()).toHaveTextContent("/menu");
});

test("#38/TC-14 ログインしていない(GET /api/me が 401)なら、メニューの画面を開くとログイン画面に移る", async () => {
  const { fetchFn, calls } = createFakeFetch({
    "GET /api/me": () => jsonResponse(401, LOGIN_REQUIRED),
    "GET /api/menu": () => jsonResponse(401, LOGIN_REQUIRED),
  });
  renderApp("/menu", fetchFn);

  await waitFor(() => expect(location()).toHaveTextContent("/login"));
  expect(screen.getByRole("button", { name: "ログイン" })).toBeInTheDocument();
  expect(calls[0]?.path).toBe("/api/me");
});

test("#38/TC-14 メニューの API の 401(時間切れ)で、ログイン画面に移る", async () => {
  const { fetchFn } = createFakeFetch({
    "GET /api/me": () => jsonResponse(200, ME),
    "GET /api/menu": () => jsonResponse(401, LOGIN_REQUIRED),
  });
  renderApp("/menu", fetchFn);

  await waitFor(() => expect(location()).toHaveTextContent("/login"));
  expect(screen.getByRole("button", { name: "ログイン" })).toBeInTheDocument();
});

test("メニューの画面でログアウトすると、ログアウトの API を JSON で呼んでログイン画面に移る", async () => {
  const user = userEvent.setup();
  const { fetchFn, calls } = createFakeFetch({
    "GET /api/me": () => jsonResponse(200, ME),
    "GET /api/menu": () => jsonResponse(200, MENU),
    "POST /api/auth/logout": () => emptyResponse(204),
  });
  renderApp("/menu", fetchFn);

  await user.click(await screen.findByRole("button", { name: "ログアウト" }));

  await waitFor(() => expect(location()).toHaveTextContent("/login"));
  const logout = calls.find((call) => call.method === "POST" && call.path === "/api/auth/logout");
  expect(logout?.contentType).toBe("application/json");
  expect(JSON.parse(logout?.body ?? "null")).toEqual({});
});

test("最初の道 / は、メニューの画面に移る", async () => {
  const { fetchFn } = createFakeFetch({
    "GET /api/me": () => jsonResponse(200, ME),
    "GET /api/menu": () => jsonResponse(200, MENU),
  });
  renderApp("/", fetchFn);

  await waitFor(() => expect(location()).toHaveTextContent("/menu"));
  expect(await screen.findByRole("region", { name: "社員" })).toBeInTheDocument();
});
