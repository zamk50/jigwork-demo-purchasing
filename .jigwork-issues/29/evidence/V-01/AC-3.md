# AC-3 (TC-3) 合格
- `git status --short` から `.jigwork/records/` を除くと、残るのは `.bashrc` 等のサンドボックスのプレースホルダー(文字デバイス、リポジトリのファイルではない)のみ。未コミットの変更なし。
- `git diff --stat 254de947bf..HEAD` は `.jigwork-issues/29/plan.md`、`docs/spec.md`、`.jigwork/records/issues/29/log.jsonl`(除外対象)のみ。docs/spec.md と .jigwork-issues/29/ 以外の変更なし。
- 見たコミット: 334554739f(docs/spec.md を入れたコミット)。`git diff --stat 254de947bf..334554739f` の出力:
  ```
   .jigwork-issues/29/plan.md           | 101 +++++++++++++++++++++++++++++++++++
   .jigwork/records/issues/29/log.jsonl |  46 ++++++++++++++++
   docs/spec.md                         |  47 ++++++++++++++++
   3 files changed, 194 insertions(+)
  ```
- その後のコミットで変わったのは `.jigwork-issues/29/evidence/V-01/`(証拠そのもの)と `.jigwork/records/`(除外)だけ。
- `git status --short` を確かめたのは証拠のファイルを書く前。いま出る `?? .jigwork-issues/29/evidence/` は証拠そのもので、検証のコミットで入る(除く)。
