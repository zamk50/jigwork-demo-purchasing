# 受入基準「ログインしていないとき」(AC-4) 判定: 合格

- 前回 V-01 からの製品のコードの差分は 3 ファイルだけ: `backend/app/seed.py`(接続に hide_parameters)・`backend/alembic/env.py`(同じ)・`backend/tests/test_i38_tc11_seed_command.py`(テスト 1 件)。この基準のコードには触れていない(`git diff 8be8809 HEAD --stat -- backend frontend` で確かめた)。
- 実行: `jig gate`(コミット 5e855a1、2026-11-08T04:42:24+09:00、テスト 153 件・失敗 0 件。[gate-run.json](gate-run.json))。テスト項目ごとの一覧と、件数から推した限界は [tc-results.md](tc-results.md)。
- この中で通った: 通し(TC-17) `frontend/e2e/i38-tc17-require-login.spec.ts` の 1 件目、API「ログインせずに呼ぶと 401」(TC-06) 4 件、「30 分と 8 時間の切れ」(TC-08) 5 件。
- 画面の単体(TC-14)の「401 でログイン画面に移る」2 件は手元の vitest でも合格([vitest-local-results.xml](vitest-local-results.xml))。
