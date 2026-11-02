# AC-4 合格
HEAD: ed5358ee48
`git diff --stat c217adb7e7 -- . ':!.jigwork/records'`:
 .jigwork-issues/32/plan.md, .jigwork-issues/32/summary-policy.md, README.md の 3 件のみ(113 insertions)。
`git diff c217adb7e7 --name-only | grep -c '^docs/spec.md'` → 0(spec.md は変わっていない)。
.jigwork/records/ は除外して判定。

追記(証拠の監査の推奨を受けて、証拠のコミットの後の HEAD 4d977c7c53 で取り直した。`git diff` は未追跡のファイルを出さないため、証拠をコミットしてから見た):
`git diff --stat c217adb7e7 -- . ':!.jigwork/records'` の出力:
```
 .jigwork-issues/32/evidence/V-01/AC-1.md |   5 ++
 .jigwork-issues/32/evidence/V-01/AC-2.md |   4 ++
 .jigwork-issues/32/evidence/V-01/AC-3.md |   3 +
 .jigwork-issues/32/evidence/V-01/AC-4.md |   6 ++
 .jigwork-issues/32/plan.md               | 101 +++++++++++++++++++++++++++++++
 .jigwork-issues/32/summary-policy.md     |  10 +++
 README.md                                |   2 +
 7 files changed, 131 insertions(+)
```
→ 証拠を足した後も、`README.md` のほかは `.jigwork-issues/32/` の中だけ。`docs/spec.md` は出ない。
