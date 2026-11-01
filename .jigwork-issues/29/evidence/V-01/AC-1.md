# AC-1 (TC-1) 合格
確かめ: docs/spec.md(HEAD 3345547)で grep -c を実行。
- `grep -c '^# '` = 1
- `grep -c '^\*\*'` = 6
- `grep -c '^- '` = 28
期待(1 / 6 / 28)と一致。
