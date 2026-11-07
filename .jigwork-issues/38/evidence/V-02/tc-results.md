# テスト項目ごとの合否(V-02)

## 出どころと限界

- `jig gate` の結果([gate-run.json](gate-run.json))は件数だけを出す: コミット 5e855a1、2026-11-08T04:42:24+09:00、テスト 153 件・失敗 0 件、手順 5 件すべて終了コード 0。
- jig gate が包みの中で書いた JUnit(`junit-pytest.xml`・`junit-vitest.xml`・`junit-playwright.xml`)は、リポジトリにも手元にも残っていなかった(ファイルシステムを名前で探して 0 件)。結果の記録の `steps[].tail` も空。そのため、jig gate の中の個々のテストの合否は読めない。
- 代わりに次の 2 つで件数を突き合わせた。
  - pytest の収集(`pytest --collect-only`、DB を立てずに流せる): 125 件([pytest-collected.txt](pytest-collected.txt))。
  - vitest 19 件(手元で流して全件合格。[vitest-local-results.xml](vitest-local-results.xml))と、Playwright 9 件(ソースの数え: `i38-tc15-menu.spec.ts` は 4 利用者の繰り返しで 4 件、TC-16・TC-18・TC-23 が 1 件ずつ、TC-17 が 2 件)。
  - 125 + 19 + 9 = 153 で、jig gate の件数と一致する。
- 飛ばしのテストがないこと: テストのソースに `skip`・`fixme`・`xfail`・`only(` は 0 件。Playwright の設定は `forbidOnly: true`・`retries: 0`。よって「153 件・失敗 0 件」は「153 件すべて流れて合格」と読む。ただし jig gate が飛ばした件数を別に出さないので、これは推論である。
- 古い `frontend/junit-playwright.xml`(2026-11-07 11:24、TC-15 の 4 件が skipped)は前の手元の実行の残りで、今の jig gate の結果ではない。証拠に使っていない。

## 一覧

判定の元: 「gate」= jig gate の失敗 0 件と件数の一致から推した合格。「手元」= 検証役の手元で流して合格(pytest は [pytest-local-sandbox-passed.log](pytest-local-sandbox-passed.log)、vitest は [vitest-local-results.xml](vitest-local-results.xml))。

| テスト項目 | 件数 | 判定 | 元 |
|---|---|---|---|
| 4 役割の API のログイン(TC-01) | pytest 5 | 合格 | gate |
| 誤ったパスワードと登録なしは同じ 401(TC-02) | pytest 2 | 合格 | gate |
| 5 回で 15 分ロック(TC-03) | pytest 10 | 合格 | gate(排他の効き目は人の報告) |
| 形の誤り・役割なしは同じ 401、照合 1 回(TC-04) | pytest 15 | 合格 | gate |
| メニューの API の出し分け(TC-05) | pytest 6 | 合格 | gate |
| ログインせずに呼ぶと 401(TC-06) | pytest 4 | 合格 | gate |
| ログアウトの後は 401(TC-07) | pytest 3 | 合格 | gate |
| 30 分と 8 時間の切れ(TC-08) | pytest 5 | 合格 | gate |
| 利用者の表はハッシュだけ(TC-09) | pytest 3 | 合格 | gate |
| 設定が無いと起動で止まる(TC-10) | pytest 12 | 合格 | 手元(12 件 PASSED)と gate |
| 初期データのコマンド(TC-11) | pytest 12(V-01 から 1 件増) | 合格 | gate |
| テーブルのコメントと戻し方(TC-12) | pytest 3 | 合格 | gate |
| ログイン画面の単体(TC-13) | vitest 9 | 合格 | 手元と gate |
| メニューの画面の単体(TC-14) | vitest 5 | 合格 | 手元と gate |
| 4 役割の通しのログインとメニュー(TC-15) | Playwright 4 | 合格 | gate |
| 誤ったパスワードの通し(TC-16) | Playwright 1 | 合格 | gate |
| ログインの守りとログアウトの通し(TC-17) | Playwright 2 | 合格 | gate |
| 幅 375px(TC-18) | Playwright 1 | 合格 | gate |
| Ruff・pyright・tsc・Oxlint(TC-19) | pytest 6 | 合格 | 手元(6 件 PASSED)と gate |
| 手順と jig gate(TC-20) | — | 合格 | [AC-8.md](AC-8.md) |
| jig check と正本(TC-21) | — | 合格(注記あり) | [AC-9.md](AC-9.md) |
| gitleaks(TC-22) | — | 合格 | [AC-6.md](AC-6.md) |
| ログインの速さ 1 秒以内(TC-23、要件 NFR-001) | Playwright 1 | 合格(測った値は見られない) | gate。下の注記 |
| TC の印のないテスト | pytest 39・vitest 5 | 合格 | gate(手元で 1 件・vitest 5 件) |

## ログインの速さ(TC-23、要件 NFR-001)

- テスト `frontend/e2e/i38-tc23-login-speed.spec.ts`: 社員 000001 で 3 回、ボタンを押してからメニューの最初の項目が出るまでを測り、中央値が 1000 ミリ秒以内であることを `expect` で確かめる。測った値は annotation と標準出力に出す。
- jig gate(コミット 5e855a1)で Playwright の手順が終了コード 0、失敗 0 件。このテストは通ったと読める。
- 測った値は取れなかった。jig gate の結果に出力の tail も JUnit も残らず、検証役の手元では PostgreSQL を立てられないため Playwright を流せない。言えるのは「jig gate の中で 1 秒の上限の検査を通った」ことだけである。
