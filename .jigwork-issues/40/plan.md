---
issue: 40
title: ログインのロックの時間を 15 分から 30 分にする
tier: major
factors: [visible, auth]
phases: [intake, policy, requirements, design, plan, implementation, verification, pr, pr_followup]
skip_reasons: {}
---

# Issue 40 ログインのロックの時間を 15 分から 30 分にする

## 理解の要約

- 何を: パスワードを続けて 5 回誤ったときのロックの時間を、15 分から 30 分にする。
- なぜ: 依頼元が、ロックの時間を延ばすことを求めているため。
- どこまで: 要件・設計・実装・テストの「15 分」を「30 分」にそろえる。テストは実装の定数を参照する形にまとめる。
- 誤る回数(5 回)・エラーの文・画面・API・テーブルは変えない。

## スコープ

- 機能要件 `docs/requirements/functions/FNC-001.md` の FR-003 の本文と、受入基準 FR-003-AC-01・FR-003-AC-02・FR-004-AC-01・FR-020-AC-01 の「15 分」を「30 分」にする。
- 方式設計 `docs/internal/architecture.md` のロックの節(135 行)の「15 分」を「30 分」にする。
- 方式設計の「差し替えの口」の項のテストの記述を、ログインの状態の 30 分とロックの 30 分を読み分けられる書き方に直す。
- 機能要件 `FNC-001.md` の「例外と境界」に、ロックの終わる時刻ちょうどの扱いと、変える前にかかったロックの扱いの 2 行を足す。
- 方式設計のロックの節に、ロックの時間を定数 1 か所で決めることと、保存済みの終わる時刻を変えないことの 2 項目を足す。
- 実装の定数 `LOCK_DURATION`(`backend/app/auth/service.py:43`)を 30 分にする。
- コードの説明文の「15 分」を直す(`backend/app/auth/service.py:10`、`backend/app/clock.py:3`、`backend/tests/clock.py:3`)。
- テスト 5 ファイルを 30 分に合わせる。定数を複製した 4 ファイルと直書きの 1 ファイルを、実装の定数を参照する形にする(作業者の質問 Q-02 の答え)。
- `backend/tests/test_i38_tc03_lock.py:175-183` の、5 分・9 分・1 分 1 秒に分けて 15 分 1 秒を進める書き方を、実装の定数から出す形にする。
- `backend/tests/test_i38_tc04_uniform_failure.py:150` の `timedelta(minutes=15, seconds=1)` を、実装の定数に 1 秒を足す形にする。
- 関数名 `test_i38_tc03_five_failures_lock_for_15_minutes`(`backend/tests/test_i38_tc03_lock.py:61`)の「15」を直す。
- 実装の定数が 30 分であることを確かめるテスト `test_i40_tc08_lock_duration_is_30_minutes` を、新しいファイル `backend/tests/test_i40_lock_duration.py` に 1 本足す(決定 D-02)。
- テストの説明文の「15 分」を直す(`backend/tests/test_i38_tc03_lock.py:1・4・5`、`backend/tests/test_i38_tc03_lock_boundary.py:3`)。

## スコープ外

- 誤る回数(5 回)は変えない。
- 既にロック中の利用者の終わる時刻は延ばさない。移行の処理は作らない(依頼元の質問 Q-01 の答え)。
- ロックの時間を設定や環境変数で変えられるようにすることは行わない。
- ログインの状態の切れ(FR-005 の 30 分)は変えない。
- 用語集の「ロック」(TRM-011)は数字を持たないため、直さない。
- 過去の Issue の記録(`.jigwork-issues/38/` の下)の「15 分」は、当時の事実の記録のため直さない。

## 受入基準

- AC-01 〔FR-003〕 前提: パスワードを続けて 5 回誤った。操作: ロックから 30 分のうちに正しいパスワードでログインする。結果: ログインできず、FR-002-AC-01 と同じエラーの文が出る。
- AC-02 〔FR-003〕 前提: ロックから 30 分が過ぎた。操作: 正しいパスワードでログインする。結果: ログインできる。
- AC-03 〔FR-004〕 前提: ロックから 30 分が過ぎた。操作: 誤ったパスワードで 1 回ログインする。結果: ロックされず、続けて 4 回誤るまでログインを試せる。
- AC-04 〔FR-020〕 前提: ロック中。操作: 誤ったパスワードで 3 回ログインし、ロックから 30 分が過ぎた後に正しいパスワードでログインする。結果: ログインできる。
- AC-05 前提: 変更後のリポジトリ。操作: `docs/requirements/functions/FNC-001.md`・`docs/internal/architecture.md`・`backend/` の下を「15 分」・`minutes=15`・`15_minutes` で検索する。結果: 当たる行が 0 件である。
- AC-06 前提: 変更後のリポジトリ。操作: ロックのテスト 5 ファイル(影響範囲の「テスト」の 5 つ)を `LOCK_DURATION =` と `timedelta(minutes=` で検索する。結果: 当たる行が 0 件で、5 ファイルとも `app.auth.service` の `LOCK_DURATION` を import している。
- AC-07 テストの手順 `.jigwork-test.json` のテストがすべて通る。
- AC-08 〔FR-003〕 前提: 変更後のリポジトリ。操作: 実装の定数 `LOCK_DURATION` を 15 分に戻してテストを流す。結果: `backend/tests/test_i40_lock_duration.py` の `test_i40_tc08_lock_duration_is_30_minutes` が落ちる。

## 影響範囲

- 文書: `docs/requirements/functions/FNC-001.md`(17〜19・21・24 行と、例外と境界の 51〜52 行)、`docs/internal/architecture.md`(ロックの節と「差し替えの口」の項)。
- コード: `backend/app/auth/service.py`(定数と説明文)、`backend/app/clock.py`(説明文)、`backend/tests/clock.py`(テストの時計の説明文)。
- テスト:
  - `backend/tests/test_i38_tc03_lock.py`
  - `backend/tests/test_i38_tc03_lock_boundary.py`
  - `backend/tests/test_i38_tc03_lock_concurrency.py`
  - `backend/tests/test_i38_tc11_seed_keeps_lock.py`
  - `backend/tests/test_i38_tc04_uniform_failure.py`
  - `backend/tests/test_i40_lock_duration.py`(新しく足す。受入基準 AC-06 の検索の外)
- 画面・帳票・API・テーブル・バッチ・外部連携・設定・権限: なし。
- 調査メモ: [R-01](research/R-01.md)。

## 前提一覧

- 🔵 ロックの時間の定義は、実装では `backend/app/auth/service.py:43` の 1 か所だけである(R-01)。
- 🔵 `users.locked_until` は終わる時刻を保存する列で、長さを持たない。テーブルの変更とマイグレーションは要らない(`backend/app/db/models.py:68`)。
- 🔵 画面と API の文言は、ロックの時間を出さない(`FNC-001.md` の FR-002、`backend/app/api/auth.py:131-132`)。
- 🔵 既にロック中の利用者は、保存済みの終わる時刻のまま解けてよい(Q-01)。
- 🔵 ロックのテストの時間の直書きは、次の 3 種類だけである。方針決めの 2 回目で全件を検索し直した。
  - 複製した定数 4 か所。
  - `test_i38_tc04_uniform_failure.py:150`。
  - `test_i38_tc03_lock.py:175-183` の分けた進め方。調査メモ R-01 はこれを見落としていた(設計の反証役の指摘)。
- 🔵 関数名の「15」は `test_i38_tc03_lock.py:61` の 1 か所だけである(方針決めの 2 回目のレビューの指摘)。
- 🔵 README・`frontend/`・`frontend/openapi.json` は、ロックの時間を書いていない。整合の観点のレビューと方針決めで「15 分」を検索し、当たらなかった。

## 質問と回答

- Q-01 【依頼元】「変更を入れた時点ですでにロック中の利用者は、保存済みの終わる時刻(ロックから 15 分後)のまま解けます。次にロックしたときから 30 分になります。この扱いでよいですか?」 回答: 「そのまま 15 分で解ける」。
- Q-02 【作業者】「テスト 4 ファイルが、ロックの時間の定数を実装から複製して持っています(1 ファイルは 15 分を直書き)。今回どこまで直しますか?」 回答: 「実装の定数を import する」。
- Q-03 【作業者】「受入基準 AC-06 と決定 D-02 の穴を、どう扱いますか?」(設計の反証役の指摘) 回答: 「方針決めへ戻して直す(推奨)」。
- Q-04 【作業者】実装計画の末に draft PR を作り、要件・設計・実装計画を見せるか(推奨は作る)。回答: 「作らない」。要件・設計・実装計画は実装前の承認で見る。

## リスク判定と実施計画

段階は重要(major)と判定する。該当した因子は次の 2 つである。

- 利用者から見える仕様の変更(visible): ロックされた利用者がログインできない時間が、15 分から 30 分に延びる。
- 認証・認可・個人情報(auth): ログインのロックは認証の制御である。ロックの時間は、パスワードを当て推量する攻撃への備えの強さを決める。

当たらない因子と根拠は次のとおりである。

- 意図の抜け(intent): 依頼の値と受入れの条件が Issue に書いてある。
- データ構造の変更・データ移行(data): テーブルは変えない。既にロック中の利用者の移行は行わない(Q-01)。
- 外部連携(external): ロックの時間を使う外部連携はない。
- 約束・予算・期限(commitment): personal のため既定でオフである。
- 影響範囲の広さ(wide): 差分は 50 行ほどの見込みである。
- 新しい作り・依存(new): 既存の定数の値を変えるだけである。

## 実施計画の推奨

- 段階: 重要。
- 通すフェーズ: 受付・方針決め・要件定義・設計・実装計画・実装・検証・PR 作成・PR 対応のすべて。
- 省くフェーズ: なし。認証(auth)に当たるため、設計は省けない。利用者から見える仕様の変更(visible)に当たるため、要件定義を通す。
- ゲート: 各フェーズで機械レビューを受ける。実装と検証はセキュリティの観点を含む精密のレビューにする。
- 承認者: 本人(personal では他者の承認も本人が押す)。
- 外部の承認: 要らない。
- マージ先: main。
- PR: 作る。

## 決定

- D-01 〔FR-003〕 既にロック中の利用者の終わる時刻は延ばさない。理由は、影響が変更の時点でロック中の利用者だけで、最大 15 分で終わるためである。選ばなかった案は、終わる時刻を延ばす移行の処理である(Q-01)。
- D-02 〔FR-003〕 ロックのテストは実装の定数 `LOCK_DURATION` を参照する。理由は、次に値を変えるときの直し漏れを防ぐためである。選ばなかった案は、各ファイルの値の置換だけである(Q-02)。
  - 定数が 30 分であることは、別のテスト 1 本で確かめる。理由は、定数だけを読むテストでは定数が何分でも通り、要件の 30 分を確かめられないためである。
  - この 1 本は設計の反証役の指摘で足した。人は方針決めへ戻して直す案を選んだ(質問 Q-03)。
- D-03 〔FR-003〕 ロックの時間は、業務の層の定数 `LOCK_DURATION` の 1 か所で決め、設定と環境変数には出さない。理由は、依頼が値の変更だけで、運用で変える求めがないためである。選ばなかった案は、設定(環境変数)で変えられるようにする案である。設定にすると、ロックを短くする誤った設定で攻撃への備えが弱まる恐れがある。

## 正本への影響

### 要件定義

- FR-003 本文の「15 分」を「30 分」にする。
- FR-003-AC-01 の「15 分」を「30 分」にする。
- FR-003-AC-02 の「15 分」を「30 分」にする。
- FR-004-AC-01 の「15 分」を「30 分」にする。
- FR-020-AC-01 の「15 分」を「30 分」にする。
- FNC-001 の「例外と境界」に、ロックの終わる時刻ちょうどの扱いと、変える前にかかったロックの扱い(Q-01)の 2 行を足す。
- 用語集(TRM)は直さない。

### 設計

- 方式設計 `docs/internal/architecture.md` のロックの節の「15 分」を「30 分」にする。同じ節に、ロックの時間を定数 1 か所で決めること(D-03)と、保存済みの終わる時刻を変えないこと(D-01)を足す。
- 同じ文書のテストの記述を、ログインの状態とロックで書き分ける。

## 実装計画

### タスク

タスクは 2 つで、T-1 を終えてから T-2 に移る。T-1 で値を変えずにテストを定数の参照へ移す。T-2 で値を 30 分にする。この順なら、各タスクの終わりでテストがすべて通る。

- T-1 〔D-02〕 テストを定数の参照に移す。ロックのテスト 5 ファイルを、実装の定数 `LOCK_DURATION` を参照する形にする。値は 15 分のまま変えない。
  - `test_i38_tc03_lock.py`・`test_i38_tc03_lock_boundary.py`・`test_i38_tc03_lock_concurrency.py`・`test_i38_tc11_seed_keeps_lock.py` の `LOCK_DURATION = timedelta(minutes=15)` を消し、`from app.auth.service import LOCK_DURATION` にする。
  - `test_i38_tc04_uniform_failure.py:150` を `clock.advance(LOCK_DURATION + timedelta(seconds=1))` にし、同じ import を足す。
  - `test_i38_tc03_lock.py:175-183` の 5 分・9 分・1 分 1 秒を、定数から出す形にする。1 回目と 2 回目は `LOCK_DURATION / 3` を進める。3 回目は `LOCK_DURATION - 2 * (LOCK_DURATION / 3) + ONE_SECOND` を進める。
  - 2 回目の確かめは、ロックの終わる時刻の手前で行う。183 行の `clock.now() == START + LOCK_DURATION + ONE_SECOND` の確かめは残す。
  - 関数名 `test_i38_tc03_five_failures_lock_for_15_minutes` を `test_i38_tc03_five_failures_lock_for_the_lock_duration` にする。
  - テストの説明文の「15 分」(`test_i38_tc03_lock.py:1・4・5`、`test_i38_tc03_lock_boundary.py:3`)を、数を書かない「ロックの時間」にする。
- T-2 〔FR-003〕〔D-02〕〔D-03〕 ロックの時間を 30 分にする。テスト先行で進める。
  - 要件定義書と方式設計は、要件定義と設計のフェーズで直し済みである。このタスクではコードだけを直す。
  - 先に `backend/tests/test_i40_lock_duration.py` に `test_i40_tc08_lock_duration_is_30_minutes` を書く。中身は `LOCK_DURATION == timedelta(minutes=30)` の 1 行である。この時点で赤になることを確かめる。
  - `backend/app/auth/service.py:43` の `LOCK_DURATION` を `timedelta(minutes=30)` にし、緑になることを確かめる。
  - 説明文の「15 分」を「30 分」にする(`backend/app/auth/service.py:10`、`backend/app/clock.py:3`、`backend/tests/clock.py:3`)。

### タスクごとの確認方法

確認のコマンドは `backend/` で流す。

- T-1: `.venv/bin/pytest -p no:cacheprovider --import-mode=importlib tests/test_i38_tc03_lock.py tests/test_i38_tc03_lock_boundary.py tests/test_i38_tc03_lock_concurrency.py tests/test_i38_tc11_seed_keeps_lock.py tests/test_i38_tc04_uniform_failure.py` がすべて通る。5 ファイルを `LOCK_DURATION =`・`timedelta(minutes=`・`15_minutes` で検索し、当たる行が 0 件である。
- T-2: 定数を変える前に `.venv/bin/pytest -p no:cacheprovider --import-mode=importlib tests/test_i40_lock_duration.py` が落ちる。定数を変えた後、`.jigwork-test.json` のテストがすべて通る。受入基準 AC-05 の 3 つの文字列で検索し、当たる行が 0 件である。`jig check` が緑である。

### テスト項目

E2E のテストのコードは書かない。画面と API の流れは変えないためである。

- TC-01 〔AC-01〕 ロック中の拒否。integration。`test_i38_tc03_five_failures_lock_for_the_lock_duration` で、ロックから `LOCK_DURATION` の 1 秒前に正しいパスワードを拒むことを確かめる。拒むときは 401 と共通のエラーの文を確かめる(`_assert_failed`、`test_i38_tc03_lock.py:51-53`)。同じテストの後半で、終わる時刻の 1 秒後にログインできることも確かめる。
- TC-02 〔AC-02〕 ロック明けのログイン。integration。`test_i38_tc03_login_at_exactly_the_lock_end_is_accepted` で、終わる時刻ちょうどにログインできることを確かめる。これは `FNC-001.md` の例外と境界の 51 行も確かめる。過ぎた後のログインは TC-01 のテストの後半が確かめる。
- TC-03 〔AC-03〕 ロック明けの 1 回の誤り。integration。`test_i38_tc03_one_failure_after_the_lock_ends_does_not_lock` で、ロック明けの 1 回の誤りでロックしないことを確かめる。
- TC-04 〔AC-04〕 ロック中の誤りを数えない。integration。`test_i38_tc03_attempts_while_locked_are_not_counted` で、ロック中の 3 回の誤りが回数に入らず、ロックの時間の後にログインできることを確かめる。
- TC-05 〔AC-05〕 「15 分」の消し残し。verify。受入基準 AC-05 の 3 つの文字列で検索し、当たる行が 0 件である。
- TC-06 〔AC-06〕 テストの定数の参照。verify。5 ファイルを検索し、当たる行が 0 件で、5 ファイルとも `LOCK_DURATION` を import している。
- TC-07 〔AC-07〕 テストの全件。verify。`.jigwork-test.json` のテストがすべて通る。
- TC-08 〔AC-08〕 定数が 30 分。unit。`test_i40_tc08_lock_duration_is_30_minutes` が、定数が 30 分のとき通り、15 分に戻すと落ちる。戻す操作は確かめの間だけ行い、コミットしない。

ロックの振る舞いのテスト(TC-01〜TC-04)は定数を参照する。ロックの時間が 30 分であることは、定数のテスト(TC-08)が確かめる。

テストの名前は、Issue 38 の既存の名前と、書式 `iN_tcNN` の新しい名前を使う。

変える前にかかったロックの扱い(`FNC-001.md` の例外と境界の 52 行、決定 D-01)には TC を付けない。理由は、移行の処理を作らないことで満たし、確かめるコードの変更がないためである。

### 実装の担い手

- 段階が重要のため、T-1 と T-2 をそれぞれ jig-implementer に任せる。

### 要件と設計とのつながり

- T-1(テストを定数の参照に移す): 決定 D-02。方式設計 `docs/internal/architecture.md` の「差し替えの口」の項のテストの記述。
- T-2(ロックの時間を 30 分にする): FR-003・FR-004・FR-020(`docs/requirements/functions/FNC-001.md`)。方式設計 `docs/internal/architecture.md` のロックの節。決定 D-02・D-03。
- ロック中の拒否(TC-01)とロック明けのログイン(TC-02)は FR-003 を確かめる。
- ロック明けの 1 回の誤り(TC-03)は FR-004 を確かめる。
- ロック中の誤りを数えない(TC-04)は FR-020 を確かめる。
- 定数が 30 分(TC-08)は FR-003 を確かめる。

## 推奨から外した箇所

- なし。
