// メニューの画面 /menu(決定 D-05「画面」。FR-012・FR-015〜FR-019)。
// 上に氏名・部署とログアウトのボタンを出す。その下に、役割ごとの見出しと項目を並べる。
// 準備中の項目は、押せないボタンに「準備中」の札を添えて出す。
import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";

import { useApi } from "@/api/ApiContext";
import { ApiError, UNEXPECTED_ERROR_MESSAGE, UnauthorizedError, type MeResponse, type MenuResponse } from "@/api/client";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";

type MenuState = { kind: "loading" } | { kind: "ready"; menu: MenuResponse } | { kind: "error"; message: string };

function messageOf(error: unknown): string {
  return error instanceof ApiError ? error.message : UNEXPECTED_ERROR_MESSAGE;
}

export function MenuPage({ me }: { me: MeResponse }) {
  const api = useApi();
  const navigate = useNavigate();
  const [state, setState] = useState<MenuState>({ kind: "loading" });
  const [loggingOut, setLoggingOut] = useState(false);
  const [logoutError, setLogoutError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    api.menu().then(
      (menu) => {
        if (active) setState({ kind: "ready", menu });
      },
      (error: unknown) => {
        if (!active || error instanceof UnauthorizedError) return;
        setState({ kind: "error", message: messageOf(error) });
      },
    );
    return () => {
      active = false;
    };
  }, [api]);

  async function handleLogout() {
    if (loggingOut) return;
    setLoggingOut(true);
    setLogoutError(null);
    try {
      await api.logout();
      await navigate("/login", { replace: true });
    } catch (error) {
      if (!(error instanceof UnauthorizedError)) {
        setLogoutError(messageOf(error));
      }
      setLoggingOut(false);
    }
  }

  return (
    <main className="mx-auto flex w-full max-w-3xl flex-col gap-6 p-4">
      <header className="flex flex-wrap items-center justify-between gap-3 border-b pb-4">
        <div className="min-w-0">
          <p className="font-bold break-words">{me.name}</p>
          <p className="text-sm text-muted-foreground">{me.department}</p>
        </div>
        <div className="flex flex-col items-end gap-1">
          {logoutError !== null && (
            <p role="alert" className="text-sm text-destructive">
              {logoutError}
            </p>
          )}
          <Button variant="outline" disabled={loggingOut} onClick={() => void handleLogout()}>
            ログアウト
          </Button>
        </div>
      </header>
      <h1 className="text-xl font-bold">メニュー</h1>
      {state.kind === "loading" && <p className="text-muted-foreground">読み込み中</p>}
      {state.kind === "error" && (
        <p role="alert" className="text-destructive">
          {state.message}
        </p>
      )}
      {state.kind === "ready" &&
        state.menu.groups.map((group) => {
          const headingId = `menu-role-${group.role.code}`;
          return (
            <section key={group.role.code} aria-labelledby={headingId} className="flex flex-col gap-2">
              <h2 id={headingId} className="text-lg font-bold">
                {group.role.name}
              </h2>
              <ul className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {group.items.map((item) => (
                  <li key={item.code}>
                    {item.available ? (
                      <Button asChild variant="outline" className="w-full justify-start">
                        <Link to={`/${item.code}`}>{item.name}</Link>
                      </Button>
                    ) : (
                      <Button variant="outline" disabled className="w-full justify-between">
                        <span>{item.name}</span>
                        <Badge>準備中</Badge>
                      </Button>
                    )}
                  </li>
                ))}
              </ul>
            </section>
          );
        })}
    </main>
  );
}
