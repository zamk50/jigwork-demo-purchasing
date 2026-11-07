# 受入基準「秘密の扱い」(AC-6) 判定: 合格

## パスワードのハッシュだけ

- `jig gate`(コミット 5e855a1、2026-11-08T04:42:24+09:00、テスト 153 件・失敗 0 件。[gate-run.json](gate-run.json))で「利用者の表はハッシュだけ」(TC-09) `backend/tests/test_i38_tc09_password_hash_only.py` の 3 件が通った。
- 移行 `backend/alembic/versions/0001_create_tables.py` は V-01 から変わっていない。users の列は `password_hash` だけ。

## 接続先とセッションの鍵は外から読み、無いと起動で止まる

- 検証役の手元で pytest を流し、「設定が無いと起動で止まる」(TC-10) `backend/tests/test_i38_tc10_startup_settings.py` の 12 件がすべて PASSED([pytest-local-sandbox-passed.log](pytest-local-sandbox-passed.log))。jig gate でも通った。
- `backend/app/settings.py` と `backend/.env.example` は V-01 から変わっていない(`git diff 8be8809 HEAD --quiet -- backend/.env.example` が差分なし)。

## gitleaks の指摘 0 件(TC-22)

- いつ・どこで: 最後のコミット 5e855a1222f4ec4c0638992987f21c5e9cc93598 の後(2026-11-08 04:41 JST)、リポジトリの直下で。gitleaks 8.30.1、`.gitleaks.toml` を使う。
- コマンド: `gitleaks git --no-banner --redact`
- 出力の要点: `105 commits scanned.` `scanned ~2311542 bytes (2.31 MB)` `no leaks found`、終了コード 0。
  - 参考: HEAD から辿れるコミットは 97(`git rev-list --count HEAD`)、全部の参照からは 109(`git rev-list --all --count`)。gitleaks は HEAD の外の参照も見ている(V-01 の 99 から増えたのは、その後のコミットと参照の分)。
- 許可の範囲(`.gitleaks.toml`): 記録のファイル `.jigwork/records/issues/<番号>/log.jsonl` の中の `key":"<64 桁の 16 進>` の形だけ(人の答え Q-23)。V-01 から変わっていない。
- この証拠の置き場の [gate-run.json](gate-run.json) には、jig gate の結果から key・content・prev を除いて写した(64 桁の 16 進は 0 件)。

## 初期データのパスワードと、初期データのコマンドの直し(TC-11、要件 NFR-006・Q-08・Q-25)

- jig gate で「初期データのコマンド」(TC-11) の 12 件が通った。V-01 の 11 件に、次の 1 件が足された(c5cb602)。
  - `backend/tests/test_i38_tc11_seed_command.py::test_i38_tc11_seed_hides_sql_values_on_an_unexpected_database_error`
  - 中身: users への INSERT を DB のトリガーで必ず失敗させ、初期データのコマンドを流す。終了コードが 0 でなく、出力にトリガーの文 `test_reject_user_insert` が出て(想定しない例外で止まった印)、社員番号 `000001`・氏名 `社員 一郎`・`$argon2id$`・4 つのパスワードのどれも出力に出ず、利用者の行が 0 件であることを確かめる。
  - このテストが jig gate の中で通ったことは、TC-11 の収集が 12 件([pytest-collected.txt](pytest-collected.txt))で、jig gate の件数が V-01 の 152 から 153 に 1 件増え、失敗 0 件であることから読む。jig gate は個々のテストの合否を出さないので、名前ごとの合格は推論である([tc-results.md](tc-results.md))。
- 直し: `backend/app/seed.py:139` が `create_engine(settings.database_url, hide_parameters=True)` になった(f962fa9)。移行 `backend/alembic/env.py:35` も同じ(edfa23d)。API `backend/app/main.py:44` は V-01 の前から付いている。`create_engine` を呼ぶ 3 か所すべてに付いていることを grep で確かめた。
- 方式設計 `docs/internal/architecture.md` の「例外とログ」に、3 つの接続が hide_parameters に従うことと、PostgreSQL の DETAIL は隠す対象の外とすること(今は決まった値しか入れないため。利用者の値を書く移行やコマンドを足すときに見直す)が書かれた(5e855a1、人の答え Q-27)。実装と食い違いはない。
- SEED_PASSWORD_EMPLOYEE / MANAGER / BUYER / ADMIN のどれかが無い・空だと止まるテスト 8 件も、jig gate で通った。
