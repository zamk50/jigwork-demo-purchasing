# AC-4 合格
- `git diff --stat 7d2fb1ed33 HEAD -- . ':!.jigwork/records'` ->
  .jigwork-issues/34/plan.md | 106 +, .jigwork-issues/34/summary-policy.md | 11 +, docs/README.md | 5 +(3 files changed, 122 insertions)。最上位 README.md と docs/spec.md は出ない。
- `git status --short` -> 追跡中の変更は .jigwork/records/issues/34/log.jsonl のみ(除外対象)。
  未追跡として .bash_profile .bashrc .gitconfig .gitmodules .idea .mcp.json .profile .ripgreprc .vscode .zprofile .zshrc が出た。これらはリポジトリ直下のホーム系の設定ファイル名で、この Issue の文書・コードの変更ではない(サンドボックス環境由来とみられ、git diff にも出ない)。
