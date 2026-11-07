# 受入基準「ログインの失敗」(AC-2) 判定: 合格

## 何を・どう確かめたか

- 実行: `jig gate`(コミット 04554da、失敗 0 件。[gate-run.json](gate-run.json))で次が通った。
  - 「誤ったパスワードと登録のない社員番号は 401 で同じ文」(TC-02) `backend/tests/test_i38_tc02_login_failure.py`
  - 「5 回で 15 分ロック」(TC-03) `test_i38_tc03_lock.py`・`test_i38_tc03_lock_boundary.py`・`test_i38_tc03_lock_concurrency.py`
  - 「形の誤りと役割なしは同じ文、照合 1 回」(TC-04) `test_i38_tc04_uniform_failure.py`・`test_i38_tc04_no_role_count.py`
  - 画面の単体「ログイン画面の入力チェックと 401 の文」(TC-13) `frontend/src/pages/LoginPage.test.tsx`。検証役の手元でも vitest 19 件・失敗 0 を確かめた([vitest-local-results.xml](vitest-local-results.xml))。
  - 通しのテスト「誤ったパスワードでログイン画面のまま誤りの文」(TC-16) `frontend/e2e/i38-tc16-login-failure.spec.ts`。文は「社員番号かパスワードが違います」。
- 排他のテストが本当に効くか: 人の端末での報告([human-report-F13-lock-concurrency.md](human-report-F13-lock-concurrency.md))。`with_for_update()` を外すと 3 回とも 2 failed。検証役は再現していない。`backend/app/auth/service.py:118` に `with_for_update()` があることは検証役も grep で確かめた。

## 何が見えたか・補足

- 「登録のない ID で画面にエラーが出る」を画面で直に通すテストはない。API は登録なしと誤ったパスワードに同じ 401 と同じ文を返し(TC-02)、画面は 401 のとき同じ誤りの文を出す(TC-13・TC-16)。この 2 つを合わせて満たすと判断した。
