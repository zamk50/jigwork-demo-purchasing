# 受入基準「ログインの失敗」(AC-2) 判定: 合格(排他の効き目は人の報告に基づく)

- 前回 V-01 からの製品のコードの差分は 3 ファイルだけ: `backend/app/seed.py`(接続に hide_parameters)・`backend/alembic/env.py`(同じ)・`backend/tests/test_i38_tc11_seed_command.py`(テスト 1 件)。この基準のコードには触れていない(`git diff 8be8809 HEAD --stat -- backend frontend` で確かめた)。
- 実行: `jig gate`(コミット 5e855a1、2026-11-08T04:42:24+09:00、テスト 153 件・失敗 0 件。[gate-run.json](gate-run.json))。テスト項目ごとの一覧と、件数から推した限界は [tc-results.md](tc-results.md)。
- この中で通った: 「誤ったパスワードと登録なしは同じ 401」(TC-02) 2 件、「5 回で 15 分ロック」(TC-03) 10 件、「形の誤り・役割なしは同じ 401」(TC-04) 15 件、通し「誤ったパスワード」(TC-16) 1 件。
- 画面の単体「ログイン画面の入力チェックと 401 の文」(TC-13) 9 件は、検証役の手元の vitest でも合格([vitest-local-results.xml](vitest-local-results.xml))。
- 排他(決定 D-08)のテストが、排他を外すと本当に落ちるか: 人(zamk50)の端末での報告に基づく([human-report-F13-lock-concurrency.md](../V-01/human-report-F13-lock-concurrency.md))。検証役は再現していない。`backend/app/auth/service.py:118` に `with_for_update()` が今もあることは grep で確かめた。
- 「登録のない ID で画面にエラー」を画面で直に通すテストはない。API が同じ 401 と同じ文を返し(TC-02)、画面が 401 で誤りの文を出す(TC-13・TC-16)ことを合わせて満たすと判断した(V-01 と同じ)。
