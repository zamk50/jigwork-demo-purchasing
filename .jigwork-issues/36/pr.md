# 文書の雛形 5 つを docs に置く

## 判断してほしいこと
- `jig template stub glossary` が、用語集の雛形と一緒に `docs/requirements/glossary.ignore.yaml`(一般の語を対象外にする一覧の初版)を作った。作業者の答え(AC を書き足す)に従い、スコープ・AC-5・TC-5 にこのファイルを足した。`docs/README.md` の一覧には載せていない。
- システム概要 `docs/requirements/overview.md` は、目的の 1 行を書き、テンプレートの空の節(H2)を残した。必須の節を消すと `jig check` が止めるため。

## 概要
導入フロー new として、文書の雛形 5 つを置き、`docs/README.md` の一覧に足した。雛形には中身(要件・設計)を書いていない。中身は最初の Issue の要件定義と設計で書く。`docs/spec.md`、最上位の `README.md`、設定、コードは変えていない。受入基準 AC-1〜5 は検証で合格(証拠: `.jigwork-issues/36/evidence/V-01/`)。
- AC-1: 雛形 5 つ(`docs/requirements/overview.md`・`nfr.md`・`glossary.yaml`、`docs/internal/architecture.md`、`docs/design/common/screen-rules.md`)がある
- AC-2: システム概要を除く 4 つに `stub: true` があり、システム概要には見出しと目的の 1 行がある
- AC-3: `docs/README.md` の一覧に 5 つが相対リンクと一言つきで載り、`spec.md` の項目も残っている
- AC-4: `jig check` が緑
- AC-5: 差分は雛形 5 つ・`glossary.ignore.yaml`・`docs/README.md`・`.jigwork-issues/36/` だけ(jig の記録を除く)

## 意思決定
なし
