---
issue: 36
title: 文書の雛形を置く
kind: onboarding
mode: new
tier: minor
factors: []
phases: [intake, policy, plan, implementation, verification, pr, pr_followup]
skip_reasons: {requirements: "雛形を置くだけで、要件の中身を書かない(最初の Issue の要件定義で書く)", design: "雛形を置くだけで、設計の中身を書かない。コードもデータ構造も変えない"}
---

# Issue 36 文書の雛形を置く

## 理解の要約

- 何を: 導入フロー new として、文書の雛形 5 つ(システム概要・非機能要件・方式設計・画面共通規則・用語集)を `docs/` の下に置く。あわせて `docs/README.md` の一覧に 5 つを足す。
- なぜ: 最初の Issue の要件定義と設計で、決まった置き場と節に中身を書けるようにするため。
- どこまで: 雛形には中身を書かない。システム概要は見出しと目的の 1〜2 行だけを書き、ほかの 4 つは `stub: true` を付ける。`docs/spec.md`・最上位の `README.md`・設定・コードは変えない。

## スコープ

- `docs/requirements/overview.md`(システム概要)を置く。`stub` は付けない。
- `docs/requirements/nfr.md`(非機能要件)を `stub: true` で置く。
- `docs/requirements/glossary.yaml`(用語集。version と空の terms と一般の語の対象外の一覧の初版)を `stub: true` で置く。
- `docs/internal/architecture.md`(方式設計)を `stub: true` で置く。
- `docs/design/common/screen-rules.md`(画面共通規則)を `stub: true` で置く。
- `docs/README.md` の一覧に、5 つの雛形を相対リンクと一言つきで足す。

## スコープ外

- 雛形に中身(要件・設計)を書くこと。最初の Issue の要件定義と設計で書く。
- `docs/spec.md` の中身を雛形に移すこと、および `docs/spec.md` を直すこと。仕様概要とシステム概要のどちらを正本にするかは、最初の Issue の要件定義で決める。
- 最上位の `README.md` を直すこと。
- 設定 `.jigwork/config.yaml` を直すこと(`docs.onboarding.mode` の既定 existing は変えない)。
- 既存の資料の棚卸し(導入フロー existing。B9)。
- コードを書くこと。

## 受入基準

- AC-1: 雛形 5 つ(`docs/requirements/overview.md`・`docs/requirements/nfr.md`・`docs/requirements/glossary.yaml`・`docs/internal/architecture.md`・`docs/design/common/screen-rules.md`)が、すべてリポジトリにある。
- AC-2: 非機能要件(`nfr.md`)・用語集(`glossary.yaml`)・方式設計(`architecture.md`)・画面共通規則(`screen-rules.md`)の 4 つに `stub: true` があり、システム概要(`overview.md`)には `stub: true` がない。`stub: true` の置き場所は、Markdown の 3 つでは先頭の frontmatter、`glossary.yaml` では最上位のキーである。確かめ方は `grep -n '^stub: true' <5 つのパス>` で、4 つに 1 行ずつ出て、`overview.md` には出ないこと。システム概要には見出しと、この文書の目的(何を書く文書か)の 1〜2 行がある。
- AC-3: `docs/README.md` の一覧に、5 つの雛形がそれぞれ相対リンクと一言つきで載り、もとの `spec.md` の項目も残っている。リンク先はすべてある。
- AC-4: `jig check` が緑である。
- AC-5: この Issue の差分は文書だけである。`git diff --stat 440931b0ae HEAD -- . ':!.jigwork/records'` に出るのが、雛形 5 つ・`docs/README.md`・`.jigwork-issues/36/` の下のファイルだけで、`docs/spec.md`・最上位の `README.md`・`.jigwork/config.yaml` が出ない。あわせて `git status --short` に、コミットしていない文書やコードの変更がない(`.jigwork/records/` は除く)。

## 影響範囲

- 画面・帳票・API・テーブル・バッチ・外部連携・権限: なし(コードがまだない)
- 設定: なし
- 文書: 新しい雛形 5 つ、`docs/README.md`
- テスト: なし(検証は `jig check` とコマンドと目視)

## 前提一覧

確かめた前提:

- 🔵 基準 `440931b0ae` の時点で、`docs/` には `README.md` と `spec.md` だけがある。5 つの置き場にファイルはない([R-01](research/R-01.md))。
- 🔵 文書の置き場の設定 `docs.root` は `docs` で、導入の mode の既定 `docs.onboarding.mode` は existing である(`jig config get`)。
- 🔵 雛形の置き場と stub の付け方は jigwork の手順に従う。
  - 置き場: jig-writing の「7. 種類(テンプレート)」の表
  - stub の付け方: jig-onboarding の「実装」の表
  - 置き方: `jig template stub` が雛形 5 つを置く(jig-writing の 7 の最後の段落)
- 🔵 設定 `docs.onboarding.mode` は直さない。根拠は jig-onboarding の「方針決め」である。mode の既定は existing のまま変えない。new はこの Issue だけの選びとして plan.md に書く。
- 🔵 システム概要の目的の 1〜2 行は、この文書が何を書く文書かだけを書き、システムの目的・使う人などの中身は書かない。`docs/spec.md` と同じ主張を書かないため、仕様概要と重ならない。中身は最初の Issue の要件定義で書く。
- 🔵 `docs/README.md` の一覧に 5 つを足す(Q-01 の答え)。
- 🔵 任意の 4 つも stub として置く(Q-02 の答え)。

仮定のまま残る前提:

- 🟡 `docs/README.md` の一覧は、`spec.md` の項目の後に 5 つを足し、どれも箇条書きの 1 行で書く。違っても書き方を直すだけで済む。

## 質問と回答

- Q-01 【作業者】docs/README.md の一覧に雛形 5 つを足すか。答え: 足す。
- Q-02 【作業者】任意の 4 つも stub として置くか。答え: 5 つとも置く。

## リスク判定と実施計画

| 因子 | 判定 | 根拠 |
|---|---|---|
| 意図の抜け(intent) | 非該当 | Issue が導入フロー new と雛形 5 つの置き場(`docs/`)を書き、手順は jigwork が決めている |
| 利用者から見える仕様の変更(visible) | 非該当 | アプリはまだなく、雛形に中身を書かない |
| データ構造の変更・データ移行(data) | 非該当 | DB もデータもない |
| 認証・認可・個人情報(auth) | 非該当 | 空の雛形だけで、個人情報を含まない |
| 外部連携(external) | 非該当 | 外部のサービスにつなぐ物を作らない |
| 約束・予算・期限への影響(commitment) | 非該当 | personal の既定でオフ |
| 影響範囲の広さ(wide) | 非該当 | 新しいファイル 5 つは雛形で、一覧の変更は数行である |
| 新しい作り・依存(new) | 非該当 | 依存を足さない。雛形は jigwork の決まった形である |

判定: **軽微(minor)**。差分の 1 文: 「文書の空の雛形 5 つを docs に置き、docs の一覧に足す」。

## 実施計画の推奨

- 段階: 軽微
- 通すフェーズ: 受付・方針決め・実装計画(plan.md の節に縮める)・実装(雛形を置く)・検証・PR 作成・PR 対応
- 省くフェーズ: 要件定義・設計(雛形だけで、要件と設計の中身は書かない)
- ゲート: 方針決めのゲート、PR 作成のゲート、最終の承認
- 承認者: 本人(zamk50)。他者の因子がないため
- 外部の承認: 要らない
- マージ先: main
- PR: 作る

## 正本への影響

### 要件定義

- 正本の ID は変えない。システム概要・非機能要件・用語集の雛形を置くが、ID を持つ中身は書かない。

### 設計

- 正本の ID は変えない。方式設計・画面共通規則の雛形を置くが、ID を持つ中身は書かない。

## 推奨から外した箇所

- なし。持ち帰り中の質問もない。
- 簡易のレビューの推奨は 3 つとも採った。AC-2 の 4 つを名指しにした(F1)。システム概要の目的の扱いを前提に書いた(F2)。手順の根拠を前提に書いた(F3)。参考の 2 件は対応が要らない。
- 因子の再判定は、8 因子のうち 7 つを非該当とした。new だけは「該当のおそれ」とし、全体の判定は軽微だった。この Issue は jigwork が決めた置き場と形の雛形を置くだけで、作りを選ぶ判断がない。そのため new は非該当とし、軽微のままにした。
