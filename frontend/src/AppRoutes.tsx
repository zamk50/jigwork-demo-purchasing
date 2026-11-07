// 画面の道(決定 D-05「画面」)。/ は /menu に移り、ログインの要る画面は守りを通す。
import { useEffect, useMemo, useState } from "react";
import { Navigate, Route, Routes, useNavigate } from "react-router-dom";

import { ApiContext } from "@/api/ApiContext";
import { createApi, UnauthorizedRelay, type FetchFn } from "@/api/client";
import { RequireLogin } from "@/auth/RequireLogin";
import { LoginPage } from "@/pages/LoginPage";
import { MenuPage } from "@/pages/MenuPage";

export function AppRoutes({ fetchFn }: { fetchFn: FetchFn }) {
  const navigate = useNavigate();
  // ログインの API でない API の 401(時間切れを含む)では、ログイン画面に移る。
  // 移る役は道が変わるたびに作り直されるので、API を呼ぶ役は作り直さずに、移る役だけを差し替える
  const [unauthorized] = useState(() => new UnauthorizedRelay());
  useEffect(() => {
    unauthorized.setHandler(() => {
      void navigate("/login", { replace: true });
    });
  }, [unauthorized, navigate]);

  const api = useMemo(() => createApi(fetchFn, () => unauthorized.fire()), [fetchFn, unauthorized]);

  return (
    <ApiContext value={api}>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/menu" element={<RequireLogin>{(me) => <MenuPage me={me} />}</RequireLogin>} />
        <Route path="*" element={<Navigate to="/menu" replace />} />
      </Routes>
    </ApiContext>
  );
}
