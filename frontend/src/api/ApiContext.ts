import { createContext, useContext } from "react";

import type { Api } from "./client";

export const ApiContext = createContext<Api | null>(null);

/** 画面の部品から API を呼ぶ役を引く。 */
export function useApi(): Api {
  const api = useContext(ApiContext);
  if (api === null) {
    throw new Error("ApiContext の中で使ってください");
  }
  return api;
}
