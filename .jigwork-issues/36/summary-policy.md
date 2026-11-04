# 方針決めの要約(Issue #36)

- 段階: **軽微(minor)**。導入フロー new として空の雛形 5 つを docs に置き、docs の一覧に足すだけです。8 因子はどれにも当たりません。
- 因子の再判定(plan.md を見ない別の役): 7 因子は非該当で一致しました。new(新しい作り)だけは「該当のおそれ」で、全体は軽微と判定しました。置き場と形は jigwork が決めていて、作りを選ぶ判断がないため、new は非該当とし軽微のままにしています。標準に上げるべきと考える場合は差し戻してください。
- 作る雛形は 5 つです。
  - システム概要 `docs/requirements/overview.md`: stub なし。見出しと文書の目的だけ
  - 非機能要件 `docs/requirements/nfr.md`: stub つき
  - 用語集 `docs/requirements/glossary.yaml`: stub つき
  - 方式設計 `docs/internal/architecture.md`: stub つき
  - 画面共通規則 `docs/design/common/screen-rules.md`: stub つき
- personal で任意の 4 つも雛形として残します(Q-02 の答え)。`docs/README.md` の一覧に 5 つを足します(Q-01 の答え)。
- 省くフェーズ: 要件定義・設計(雛形だけで、中身は最初の Issue で書く)。
- 推奨から外した所: なし。
- 仮定のまま残る前提(🟡): 一覧の 5 つは `spec.md` の項目の後に箇条書きの 1 行ずつで足す。
- レビュー: 必須の指摘はありません。推奨の 3 件は直しました。参考の 2 件は対応不要です。
- 持ち帰り中の質問: なし。
