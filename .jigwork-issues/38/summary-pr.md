# PR の要約(Issue 38)

- 変えたもの: 107 ファイル、約 11,300 行の追加。API のサーバー `backend/`、画面 `frontend/`、正本の文書 `docs/` である。行の多くはロックファイル(`frontend/pnpm-lock.yaml`・`backend/uv.lock`)と生成した型。
- 受入基準 9 つ(AC-1〜AC-9)は、検証(V-02)ですべて合格。証拠は [evidence/V-02/README.md](evidence/V-02/README.md)。jig gate はテスト 153 件で失敗 0 件、gitleaks の指摘は 0 件。
- 人の報告に頼った合格: ログインの失敗(AC-2)のロックの排他は、人が手元で流した報告が根拠。検証役のサンドボックスでは DB を使うテストを流せなかった。
- 測れていない値: ログインの速さ(TC-23)は 1 秒の上限を通ったことだけが言え、測った値はない。
- 仮のまま残る点: 初期データの氏名と部署(A-12)、本番の PostgreSQL 18(A-16)、行の数(A-17)。一覧は [assumptions.yaml](assumptions.yaml)。
- 推奨から外した所: Issue を分割していない。途中の draft PR を作っていない(Q-18)。
