# docs の文書の一覧 docs/README.md を置く

## 判断してほしいこと
- 一覧は見出し・1 行の説明・文書ごとの箇条書きの形で、今は `spec.md` の 1 項目だけ。`docs/README.md` 自身と、最上位の `README.md` へ戻るリンクは載せていない(方針決めの仮定とスコープ外のとおり)。
- `spec.md` の一言は「仕様概要。…目的・使う人・業務の流れ・欲しい機能などをまとめた文書」。「データの量」「守ってほしいこと」の節は「など」に含めた。

## 概要
`docs/README.md` を新しく作り、docs フォルダの文書の一覧(今は仕様概要 `docs/spec.md` の 1 つ)を、何の文書かの一言と相対リンクつきで書いた。最上位の `README.md`、`docs/spec.md`、コードは変えていない。受入基準 AC-1〜4 は検証で合格(証拠: `.jigwork-issues/34/evidence/V-01/`)。
- AC-1: `docs/README.md` に `spec.md` への相対リンクがあり、リンク先がある(`jig check` も緑)
- AC-2: `spec.md` の項目に「仕様概要」の語がある
- AC-3: 基準のコミットの時点で docs にある文書(`spec.md`)が漏れなく載っている
- AC-4: 変わったのは `docs/README.md` と `.jigwork-issues/34/` だけ(jig の記録を除く)

## 意思決定
なし
