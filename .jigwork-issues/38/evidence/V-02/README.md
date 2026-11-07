# Issue #38 の検証(V-02) 証拠の一覧

- 対象: 基準のコミット a83138e49b から HEAD(5e855a1222f4ec4c0638992987f21c5e9cc93598)まで。
  - V-01(コミット 04554da で検証)の後に変わった製品のコードは、`backend/app/seed.py`・`backend/alembic/env.py`・`backend/tests/test_i38_tc11_seed_command.py` の 3 ファイル。文書は `docs/internal/architecture.md` と `.jigwork-issues/38/plan.md`。
  - V-01 の証拠は書き換えていない。変わっていない部分の突き合わせは V-01 の各ファイルを指す。
- 検証役の環境の制約: サンドボックスでは PostgreSQL が Unix ソケットを作れず(Operation not permitted)、DB を使う pytest と Playwright は手元で流せない。実行の主な証拠は `jig gate` の結果。
- `jig gate`: V-02 で検証役が流した最後の実行は、コミット 5e855a1、2026-11-08T04:42:24+09:00。ok、テスト 153 件・失敗 0 件、止める項目 0 件([gate-run.json](gate-run.json)。key などを除いて写した)。
- 秘密の走査: 5e855a1 の後に `gitleaks git --no-banner --redact` で 105 コミットを走査し、指摘 0 件([AC-6.md](AC-6.md))。
- テスト項目ごとの合否と、件数から推した限界: [tc-results.md](tc-results.md)。jig gate は個々の合否を出さず、JUnit も残らないので、名前ごとの合格は件数の一致(pytest 125 + vitest 19 + Playwright 9 = 153)と失敗 0 件からの推論である。
- 手元で流せた分: pytest 19 件合格([pytest-local-sandbox-passed.log](pytest-local-sandbox-passed.log))・vitest 19 件合格([vitest-local-results.xml](vitest-local-results.xml))・pytest の収集 125 件([pytest-collected.txt](pytest-collected.txt))。

| 受入基準 | 判定 | 証拠 |
|---|---|---|
| ログインとメニュー(AC-1) | 合格 | [AC-1.md](AC-1.md) |
| ログインの失敗(AC-2) | 合格(排他の効き目は人の報告に基づく) | [AC-2.md](AC-2.md)・[human-report-F13-lock-concurrency.md](../V-01/human-report-F13-lock-concurrency.md) |
| 役割による出し分け(AC-3) | 合格 | [AC-3.md](AC-3.md) |
| ログインしていないとき(AC-4) | 合格 | [AC-4.md](AC-4.md) |
| ログアウト(AC-5) | 合格 | [AC-5.md](AC-5.md) |
| 秘密の扱い(AC-6) | 合格(足したテストの合格は件数からの推論) | [AC-6.md](AC-6.md) |
| テーブルの論理名(AC-7) | 合格 | [AC-7.md](AC-7.md) |
| テストと検査(AC-8) | 合格 | [AC-8.md](AC-8.md) |
| 正本の文書(AC-9) | 合格(全体の jig check は汚れた作業ツリーで流せず、gate と文書の検査の 2 つから判断) | [AC-9.md](AC-9.md) |

ログインの速さ(TC-23、要件 NFR-001)は受入基準に紐づかないテスト項目で、jig gate の中で 1 秒の上限の検査を通ったことだけが言え、測った値は取れなかった([tc-results.md](tc-results.md))。
