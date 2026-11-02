# AC-2 合格
HEAD: ed5358ee48
足した行は README.md 5 行目の 1 行のみ(空行を除く): `仕様概要は [docs/spec.md](docs/spec.md) にあります。`
「仕様概要」と `docs/spec.md` の両方を含む。1〜3 行の範囲内。

追記(証拠の監査の推奨を受けて、HEAD 4d977c7c53 で取り直した):
`git diff c217adb7e7 -- README.md | grep '^+[^+]'` の出力(空行を除く追加の行):
```
+仕様概要は [docs/spec.md](docs/spec.md) にあります。
```
→ 1 行。「仕様概要」と `docs/spec.md` をどちらも含む。
