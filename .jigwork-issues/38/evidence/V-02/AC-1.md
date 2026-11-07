# 受入基準「ログインとメニュー」(AC-1) 判定: 合格

- 前回 V-01 からの製品のコードの差分は 3 ファイルだけ: `backend/app/seed.py`(接続に hide_parameters)・`backend/alembic/env.py`(同じ)・`backend/tests/test_i38_tc11_seed_command.py`(テスト 1 件)。この基準のコードには触れていない(`git diff 8be8809 HEAD --stat -- backend frontend` で確かめた)。
- 実行: `jig gate`(コミット 5e855a1、2026-11-08T04:42:24+09:00、テスト 153 件・失敗 0 件。[gate-run.json](gate-run.json))。テスト項目ごとの一覧と、件数から推した限界は [tc-results.md](tc-results.md)。
- この中で通った: 通しのテスト「4 役割が画面でログインし項目表と一致」(TC-15) `frontend/e2e/i38-tc15-menu.spec.ts` の 4 件、API「ログインとログイン中の利用者」(TC-01) `backend/tests/test_i38_tc01_login_and_me.py` ほか 5 件、「幅 375px」(TC-18) 1 件。
- 突き合わせ(項目表 FR-016 `docs/requirements/functions/FNC-003.md` と、コードの MENU_TABLE と、テストの期待)は V-01 の [AC-1.md](../V-01/AC-1.md) のとおりで、その後この 3 つのファイルは変わっていない。
- 注記: 「ID」は社員番号で返る(要件 FR-001・FR-009 の決めどおり)。TC-01・TC-15 は検証役の手元では流せない(DB を立てられない)。
