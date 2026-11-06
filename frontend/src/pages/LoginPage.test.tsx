// @vitest-environment jsdom
// #38/TC-13: ログイン画面で、空の欄と 6 桁でない社員番号は API を呼ばずに欄の下に文を出す。
// 401 では画面が移らずに誤りの文を出す。送信中はボタンを押せない。
import { cleanup, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, test } from "vitest";

import {
  createFakeFetch,
  deferred,
  jsonResponse,
  renderApp,
  type ApiCall,
  type MeResponse,
  type MenuResponse,
} from "@/testing/fakeApi";

afterEach(cleanup);

const LOGIN = "POST /api/auth/login";
const LOGIN_FAILED = "社員番号かパスワードが違います";

const ME: MeResponse = {
  employee_no: "000001",
  name: "社員 一郎",
  department: "総務部",
  roles: [{ code: "employee", name: "社員" }],
};

const MENU: MenuResponse = {
  groups: [
    {
      role: { code: "employee", name: "社員" },
      items: [{ code: "item_search", name: "品目の検索", available: false }],
    },
  ],
};

function employeeNoInput() {
  return screen.getByLabelText("社員番号");
}

function passwordInput() {
  return screen.getByLabelText("パスワード");
}

function loginButton() {
  return screen.getByRole("button", { name: "ログイン" });
}

function loginCalls(calls: ApiCall[]) {
  return calls.filter((call) => `${call.method} ${call.path}` === LOGIN);
}

test("#38/TC-13 社員番号とパスワードが空なら、API を呼ばずに両方の欄の下に「入力してください」を出す", async () => {
  const user = userEvent.setup();
  const { fetchFn, calls } = createFakeFetch({});
  renderApp("/login", fetchFn);

  await user.click(loginButton());

  expect(employeeNoInput()).toHaveAccessibleDescription("入力してください");
  expect(passwordInput()).toHaveAccessibleDescription("入力してください");
  expect(calls).toHaveLength(0);
});

test("#38/TC-13 パスワードだけが空なら、API を呼ばずにパスワードの欄の下に入力を求める文を出す", async () => {
  const user = userEvent.setup();
  const { fetchFn, calls } = createFakeFetch({});
  renderApp("/login", fetchFn);

  await user.type(employeeNoInput(), "000001");
  await user.click(loginButton());

  expect(passwordInput()).toHaveAccessibleDescription("入力してください");
  expect(employeeNoInput()).not.toHaveAccessibleDescription("入力してください");
  expect(calls).toHaveLength(0);
});

test.each(["12345", "1234567", "12345a", "１２３４５６"])(
  "#38/TC-13 社員番号が数字 6 桁でない(%s)なら、API を呼ばずに社員番号の欄の下に形の誤りを出す",
  async (employeeNo) => {
    const user = userEvent.setup();
    const { fetchFn, calls } = createFakeFetch({});
    renderApp("/login", fetchFn);

    await user.type(employeeNoInput(), employeeNo);
    await user.type(passwordInput(), "secret-password");
    await user.click(loginButton());

    expect(employeeNoInput()).toHaveAccessibleDescription("数字 6 桁で入れてください");
    expect(calls).toHaveLength(0);
  },
);

test("#38/TC-13 社員番号の欄は数字のキーボードを出し、パスワードの欄は文字を伏せる", () => {
  const { fetchFn } = createFakeFetch({});
  renderApp("/login", fetchFn);

  expect(employeeNoInput()).toHaveAttribute("inputmode", "numeric");
  expect(passwordInput()).toHaveAttribute("type", "password");
});

test("#38/TC-13 ログインの API の 401 では、画面が移らずにボタンの上に誤りの文を出す", async () => {
  const user = userEvent.setup();
  const { fetchFn, calls } = createFakeFetch({
    [LOGIN]: () => jsonResponse(401, { detail: LOGIN_FAILED }),
  });
  renderApp("/login", fetchFn);

  await user.type(employeeNoInput(), "000001");
  await user.type(passwordInput(), "wrong-password");
  await user.click(loginButton());

  const alert = await screen.findByRole("alert");
  expect(alert).toHaveTextContent(LOGIN_FAILED);
  // 誤りの文はボタンの上(文書の順でボタンより前)に出す
  expect(alert.compareDocumentPosition(loginButton()) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
  expect(screen.getByTestId("location")).toHaveTextContent("/login");
  expect(loginCalls(calls)).toHaveLength(1);
  expect(loginCalls(calls)[0]?.contentType).toBe("application/json");
  expect(JSON.parse(loginCalls(calls)[0]?.body ?? "null")).toEqual({
    employee_no: "000001",
    password: "wrong-password",
  });
});

test("#38/TC-13 送信中はログインのボタンを押せず、応答が返ると押せるようになる", async () => {
  const user = userEvent.setup();
  const pending = deferred<Response>();
  const { fetchFn, calls } = createFakeFetch({ [LOGIN]: () => pending.promise });
  renderApp("/login", fetchFn);

  await user.type(employeeNoInput(), "000001");
  await user.type(passwordInput(), "wrong-password");
  await user.click(loginButton());

  expect(loginButton()).toBeDisabled();
  await user.click(loginButton());
  expect(loginCalls(calls)).toHaveLength(1);

  pending.resolve(jsonResponse(401, { detail: LOGIN_FAILED }));
  await waitFor(() => expect(loginButton()).toBeEnabled());
  expect(loginCalls(calls)).toHaveLength(1);
});

test("ログインに成功すると、メニューの画面に移る", async () => {
  const user = userEvent.setup();
  const { fetchFn } = createFakeFetch({
    [LOGIN]: () => jsonResponse(200, ME),
    "GET /api/me": () => jsonResponse(200, ME),
    "GET /api/menu": () => jsonResponse(200, MENU),
  });
  renderApp("/login", fetchFn);

  await user.type(employeeNoInput(), "000001");
  await user.type(passwordInput(), "right-password");
  await user.click(loginButton());

  await waitFor(() => expect(screen.getByTestId("location")).toHaveTextContent("/menu"));
});

test.each([
  ["500 の応答", () => jsonResponse(500, { detail: "時間をおいてもう一度試してください" })],
  ["通信の失敗", () => Promise.reject(new TypeError("Failed to fetch"))],
])("ログインで想定しない誤り(%s)なら、共通の文を出して画面は移らない", async (_name, handler) => {
  const user = userEvent.setup();
  const { fetchFn } = createFakeFetch({ [LOGIN]: handler });
  renderApp("/login", fetchFn);

  await user.type(employeeNoInput(), "000001");
  await user.type(passwordInput(), "some-password");
  await user.click(loginButton());

  expect(await screen.findByRole("alert")).toHaveTextContent("時間をおいてもう一度試してください");
  expect(screen.getByTestId("location")).toHaveTextContent("/login");
  await waitFor(() => expect(loginButton()).toBeEnabled());
});
