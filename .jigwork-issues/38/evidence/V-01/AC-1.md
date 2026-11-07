# 受入基準「ログインとメニュー」(AC-1) 判定: 合格

## 何を・どう確かめたか

- 実行: `jig gate`(コミット 04554da、テスト 152 件・失敗 0 件。[gate-run.json](gate-run.json))。次のテストがこの中で通った。
  - 通しのテスト「4 役割が画面でログインし項目表と一致」(TC-15) `frontend/e2e/i38-tc15-menu.spec.ts`: 000001〜000004 の 4 件。ログイン画面で社員番号とパスワードを入れ、`/menu` に移り見出し「メニュー」が出る。役割の見出しと項目が、項目表(FR-016)の行と数・順・名前で一致する。
  - API のテスト「ログインとログイン中の利用者」(TC-01) `backend/tests/test_i38_tc01_login_and_me.py`: 移行と初期データのコマンドで入れた DB で 4 人がログインでき、`/api/me` が社員番号・氏名・部署・役割を返す。000002 は社員と上長の 2 役割。
  - 通しのテスト「幅 375px ではみ出さない」(TC-18) `frontend/e2e/i38-tc18-narrow-width.spec.ts`。
- 突き合わせ: テストの期待の項目は、項目表 `docs/requirements/functions/FNC-003.md` の FR-016 と同じ。コードの定数 `backend/app/menu/service.py` の MENU_TABLE も同じ並びと名前(目で比べた)。初期データの 4 人は `docs/internal/architecture.md` の「初期データ」の表と TC-01 の期待が同じ。

## 何が見えたか

- gate の Playwright の手順は終了コード 0。e2e のソースに skip / fixme はなく、`forbidOnly: true`・`retries: 0`。
- 注意: 「ID」は社員番号(employee_no)で返る。内部の利用者 ID(users.id)は返さない。要件 FR-001・FR-009 で ID は社員番号と決めてあるので、基準の「ID」を満たすと判断した。
- 検証役の手元では DB を立てられず、TC-01・TC-15 を自分では流していない(README を参照)。
