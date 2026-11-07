# Issue #38 の検証(V-01) 証拠の一覧

- 対象: 基準のコミット a83138e49b から HEAD(04554da6c4)まで。製品のコードは 8be8809 と同じ(04554da は証拠と記録だけを足したコミット)。
- 検証役の環境の制約: 検証役のサンドボックスでは PostgreSQL が Unix ソケットを作れず(Operation not permitted)、DB を使う pytest と Playwright は手元で流せなかった。
  そのため実行の証拠は、jig が自分の包みの中で流した `jig gate` の結果([gate-run.json](gate-run.json))を主にした。手元で流せた分は [pytest-local-sandbox.log](pytest-local-sandbox.log)・[vitest-local-results.xml](vitest-local-results.xml)。
- `jig gate` は 2 回走った(20:27:47 にコミット 8be8809、20:29:08 にコミット 04554da)。どちらも ok、テスト 152 件・失敗 0 件、止める項目 0 件。
  内訳(テストの名前の数からの推定): pytest 124・vitest 19・Playwright 9。
- jig gate の結果には、個々のテストの合否は出ない(件数だけ)。個々のテストが何を確かめるかは、テストのソースを読んで突き合わせた。

| 受入基準 | 判定 | 証拠 |
|---|---|---|
| ログインとメニュー(AC-1) | 合格 | [AC-1.md](AC-1.md) |
| ログインの失敗(AC-2) | 合格 | [AC-2.md](AC-2.md)・[human-report-F13-lock-concurrency.md](human-report-F13-lock-concurrency.md) |
| 役割による出し分け(AC-3) | 合格 | [AC-3.md](AC-3.md) |
| ログインしていないとき(AC-4) | 合格 | [AC-4.md](AC-4.md) |
| ログアウト(AC-5) | 合格 | [AC-5.md](AC-5.md) |
| 秘密の扱い(AC-6) | 合格 | [AC-6.md](AC-6.md) |
| テーブルの論理名(AC-7) | 合格 | [AC-7.md](AC-7.md) |
| テストと検査(AC-8) | 合格 | [AC-8.md](AC-8.md) |
| 正本の文書(AC-9) | 合格 | [AC-9.md](AC-9.md) |
