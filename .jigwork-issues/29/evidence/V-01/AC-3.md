# AC-3 (TC-3) 合格
- `git status --short` から `.jigwork/records/` を除くと、残るのは `.bashrc` 等のサンドボックスのプレースホルダー(文字デバイス、リポジトリのファイルではない)のみ。未コミットの変更なし。
- `git diff --stat 254de947bf..HEAD` は `.jigwork-issues/29/plan.md`、`docs/spec.md`、`.jigwork/records/issues/29/log.jsonl`(除外対象)のみ。docs/spec.md と .jigwork-issues/29/ 以外の変更なし。
