# 受入基準「ログアウト」(AC-5) 判定: 合格

- 前回 V-01 からの製品のコードの差分は 3 ファイルだけ: `backend/app/seed.py`(接続に hide_parameters)・`backend/alembic/env.py`(同じ)・`backend/tests/test_i38_tc11_seed_command.py`(テスト 1 件)。この基準のコードには触れていない(`git diff 8be8809 HEAD --stat -- backend frontend` で確かめた)。
- 実行: `jig gate`(コミット 5e855a1、2026-11-08T04:42:24+09:00、テスト 153 件・失敗 0 件。[gate-run.json](gate-run.json))。テスト項目ごとの一覧と、件数から推した限界は [tc-results.md](tc-results.md)。
- この中で通った: 通し(TC-17) の 2 件目(ログアウトの後に `/menu` を開くと `/login` に移る)、API「ログアウトの後は 401」(TC-07) `test_i38_tc07_logout.py`・`test_i38_tc07_menu_after_logout.py` の 3 件。
