// ログインの要る画面の守り(FR-007。画面共通規則の「時間切れ」)。
// 画面を開いたら、まず GET /api/me を呼ぶ。401 なら API を呼ぶ役がログイン画面に移す。
import { useEffect, useState, type ReactNode } from "react";

import { useApi } from "@/api/ApiContext";
import { ApiError, UNEXPECTED_ERROR_MESSAGE, UnauthorizedError, type MeResponse } from "@/api/client";

type State = { kind: "loading" } | { kind: "ready"; me: MeResponse } | { kind: "error"; message: string };

export function RequireLogin({ children }: { children: (me: MeResponse) => ReactNode }) {
  const api = useApi();
  const [state, setState] = useState<State>({ kind: "loading" });

  useEffect(() => {
    let active = true;
    api.me().then(
      (me) => {
        if (active) setState({ kind: "ready", me });
      },
      (error: unknown) => {
        if (!active || error instanceof UnauthorizedError) return;
        setState({ kind: "error", message: error instanceof ApiError ? error.message : UNEXPECTED_ERROR_MESSAGE });
      },
    );
    return () => {
      active = false;
    };
  }, [api]);

  if (state.kind === "ready") {
    return children(state.me);
  }
  if (state.kind === "error") {
    return (
      <main className="mx-auto w-full max-w-3xl p-4">
        <p role="alert" className="text-destructive">
          {state.message}
        </p>
      </main>
    );
  }
  return (
    <main className="mx-auto w-full max-w-3xl p-4">
      <p className="text-muted-foreground">読み込み中</p>
    </main>
  );
}
