# 受入基準「ログアウト」(AC-5) 判定: 合格

- 実行: `jig gate`(失敗 0 件。[gate-run.json](gate-run.json))で次が通った。
  - 通しのテスト(TC-17の 2 件目) `frontend/e2e/i38-tc17-require-login.spec.ts`: 000002 でログインしてログアウトすると `/login` に移り、その後 `/menu` を開いても `/login` に移る。
  - API(TC-07) `backend/tests/test_i38_tc07_menu_after_logout.py`・`test_i38_tc07_logout.py`: ログアウトは 204、その後のメニューの API は 401、前のクッキーを付け直しても 401。ログインの状態がなくてもログアウトは 204。
