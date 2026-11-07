import { BrowserRouter } from "react-router-dom";

import type { FetchFn } from "@/api/client";
import { AppRoutes } from "@/AppRoutes";

const browserFetch: FetchFn = (path, init) => fetch(path, init);

export function App({ fetchFn = browserFetch }: { fetchFn?: FetchFn }) {
  return (
    <BrowserRouter>
      <AppRoutes fetchFn={fetchFn} />
    </BrowserRouter>
  );
}
