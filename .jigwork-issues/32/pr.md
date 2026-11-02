# README に仕様概要 docs/spec.md への案内を足す

## 判断してほしいこと
- 案内は README の末尾に空行を 1 つ挟んで 1 行で足し、小見出しは付けていない(方針決めの仮定のとおり)。置き場を変えたければ行を動かすだけで済む。
- 案内の文は「仕様概要は [docs/spec.md](docs/spec.md) にあります。」で、spec.md が何を扱うか(購買と在庫のシステム)までは書いていない。Issue の求めは満たしている。

## 概要
README.md の末尾に、仕様概要 docs/spec.md への相対リンクを含む案内を 1 行足した。今ある README の文、docs/spec.md、コードは変えていない。受入基準 AC-1〜4 は検証で合格(証拠: .jigwork-issues/32/evidence/V-01/)。
- AC-1: README に `](docs/spec.md)` があり、リンク先がある
- AC-2: 足した案内は 1 行で、「仕様概要」と `docs/spec.md` を含む
- AC-3: README の差分は追加の行だけ
- AC-4: 変わったのは README.md と .jigwork-issues/32/ だけ(jig の記録を除く)

## 意思決定
なし
