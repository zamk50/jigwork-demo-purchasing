# 受入基準「ログインしていないとき」(AC-4) 判定: 合格

- 実行: `jig gate`(失敗 0 件。[gate-run.json](gate-run.json))で次が通った。
  - 通しのテスト(TC-17) `frontend/e2e/i38-tc17-require-login.spec.ts`: ログインせずに `/menu` を開くと `/login` に移り見出し「ログイン」が出る。
  - API(TC-06) `backend/tests/test_i38_tc06_requires_login.py`・`test_i38_tc06_menu_requires_login.py`: ログインせずに `/api/me` と `/api/menu` を呼ぶと 401。知らないクッキーでも 401。
  - 時間切れ(TC-08) `test_i38_tc08_session_timeout.py`: 操作なし 30 分超・ログインから 8 時間超で 401。
  - 画面の単体(TC-14): `/api/me` の 401 と、メニューの API の 401 でログイン画面に移る(手元の vitest でも通過。[junit-vitest-local.xml](junit-vitest-local.xml))。
