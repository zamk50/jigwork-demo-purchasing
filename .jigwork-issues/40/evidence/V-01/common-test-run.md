# 検証 V-01 の共通: テストの全件の実行

AC-01〜AC-04・AC-07 の証拠が共通に使う実行の記録である。

## 対象

- 製品のコードの最後のコミット: 8ed42a471df7b2120e2b986d4892234c59e6772e。基準のコミット: 0eed1c95fcf57e35b5f076cc19c9c67e4b64f940。
- 作業ツリーの変更は `.jigwork/records/issues/40/log.jsonl` だけで、製品のコードとテストは 8ed42a4 と同じ。
- 8ed42a4 の後のコミット c6d7011 と b8e239b で変わったのは、この証拠のファイル(`.jigwork-issues/40/evidence/V-01/`)と jig の記録だけである(`git diff --stat 8ed42a4 b8e239b` で確かめた)。製品のコードとテストは変わっていない。
- 証拠を置いた後の HEAD b8e239b でも `jig check` を流し、テストのゲートが緑(手順 5 件のうち失敗 0 件)、文書の検査が緑だった。

## 1. 検証役のサンドボックスでの直の実行(参考。判定には使わない)

```
cd backend && .venv/bin/pytest -v -ra -p no:cacheprovider --import-mode=importlib --junitxml=<scratchpad>/junit-pytest.xml
```

- 結果: 20 passed, 106 errors。
- errors の原因は全件同じで、テストの土台(`backend/tests/conftest.py` の `postgres_server`)が一時の PostgreSQL を立てられなかった。
  サーバーのログ: `could not create Unix socket for address "<scratchpad>/pg-.../.s.PGSQL.5432": Operation not permitted`。
- 検証役のサンドボックスが Unix ソケットを作らせないためで、製品やテストの不具合ではない。

## 2. jig のテストのゲート(判定に使う)

```
~/.local/share/jigwork/bin/jig check --json
```

- 記録 `gate.test`(seq 263、2026-11-16T18:20:18+09:00): `ok: true`、`commit: 8ed42a4…`、`tests: 154`、`failed: 0`。
- 手順(`.jigwork-test.json` の test の 3 つ)はすべて exit 0:
  - `cd backend && .venv/bin/pytest -v -ra -p no:cacheprovider --import-mode=importlib --junitxml=junit-pytest.xml` → exit 0
  - `cd frontend && pnpm exec vitest run ...` → exit 0
  - `cd frontend && pnpm exec playwright test` → exit 0
- install の 2 手順も exit 0。`blocked: []`。
- 弱めの検出(weaken)は、W13・W2・W6(block)がすべて `passed: true`、ほかは review の注意だけ。
  - W2 は関数名の変更(`..._for_15_minutes` → `..._for_the_lock_duration`)、W6 は 5 分・9 分・15 分の直書きを定数の参照に変えたことで、計画 T-1 のとおり。
- 記録 `check.docs`(seq 265): `ok: true`、`blocked: []`。指摘は plan.md の引用の文体(warn)4 件だけ。

## 3. 対象のテストが集められること(DB なしで確かめられる範囲)

```
cd backend && .venv/bin/pytest -p no:cacheprovider --import-mode=importlib --collect-only -q tests/test_i38_tc03_lock.py tests/test_i38_tc03_lock_boundary.py tests/test_i40_lock_duration.py
```

- `test_i38_tc03_five_failures_lock_for_the_lock_duration`・`test_i38_tc03_one_failure_after_the_lock_ends_does_not_lock`・`test_i38_tc03_attempts_while_locked_are_not_counted`・`test_i38_tc03_login_at_exactly_the_lock_end_is_accepted`・`test_i40_tc08_lock_duration_is_30_minutes` を含む 9 件が集められた。
- よって 2 の 154 件・失敗 0 件に、これらのテストが含まれる。

## 限り

- jig の記録は件数と終了コードだけで、テストごとの通過の一覧は残らない(junit の xml は作業ツリーに残っていない)。上の 3 と合わせて、対象のテストが通ったと判断した。
- `backend/app` と `backend/tests` の `.py` に `skip`・`xfail` の当たりは 0 件である。よって 154 件・失敗 0 件の中に、黙って飛ばされたテストは隠れていない。
- したがって AC-01〜AC-04 の合格は、テストごとの結果ではなく、全体の件数からの推論である。

## ロック中かどうかを外から見分けられないこと(セキュリティの負のケース)

#38 からあるテストのうち、次も 154 件・失敗 0 件の中で通った(同じく全体の件数からの推論)。ロックの時間は実装の定数 `LOCK_DURATION` を使い、30 分で確かめている。

- `test_i38_tc04_failure_bodies_are_identical`(`backend/tests/test_i38_tc04_uniform_failure.py:158`): ロック中も含め、失敗の本文が同じである。
- `test_i38_tc04_every_failure_and_success_verifies_once`(同 126 行): ロック中もパスワードの照合を 1 回行う。
- `test_i38_tc03_lock_is_per_user`(`backend/tests/test_i38_tc03_lock.py:90`): ロックは社員番号ごとである。
- `test_i38_tc03_unknown_employee_no_is_never_locked`(同 190 行): 登録のない社員番号はロックされない。
