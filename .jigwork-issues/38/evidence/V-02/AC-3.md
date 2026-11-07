# 受入基準「役割による出し分け」(AC-3) 判定: 合格

- 前回 V-01 からの製品のコードの差分は 3 ファイルだけ: `backend/app/seed.py`(接続に hide_parameters)・`backend/alembic/env.py`(同じ)・`backend/tests/test_i38_tc11_seed_command.py`(テスト 1 件)。この基準のコードには触れていない(`git diff 8be8809 HEAD --stat -- backend frontend` で確かめた)。
- 実行: `jig gate`(コミット 5e855a1、2026-11-08T04:42:24+09:00、テスト 153 件・失敗 0 件。[gate-run.json](gate-run.json))。テスト項目ごとの一覧と、件数から推した限界は [tc-results.md](tc-results.md)。
- この中で通った: API「メニューは役割の行だけ」(TC-05) `backend/tests/test_i38_tc05_menu.py` 6 件、通し(TC-15) 4 件。画面の単体(TC-14) 5 件は手元の vitest でも合格([vitest-local-results.xml](vitest-local-results.xml))。
- コードと項目表の突き合わせは V-01 の [AC-3.md](../V-01/AC-3.md) のとおり(`backend/app/menu/service.py` は V-01 から変わっていない)。
