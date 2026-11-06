// 骨組み: 実装の前に置く。中身は実装のコミットで書く
/** API を呼ぶ役。画面には props で渡し、テストでは決めた応答を返すものに差し替える。 */
export type FetchFn = (path: string, init?: RequestInit) => Promise<Response>;
