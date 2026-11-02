# AC-4 合格
HEAD: ed5358ee48
`git diff --stat c217adb7e7 -- . ':!.jigwork/records'`:
 .jigwork-issues/32/plan.md, .jigwork-issues/32/summary-policy.md, README.md の 3 件のみ(113 insertions)。
`git diff c217adb7e7 --name-only | grep -c '^docs/spec.md'` → 0(spec.md は変わっていない)。
.jigwork/records/ は除外して判定。
