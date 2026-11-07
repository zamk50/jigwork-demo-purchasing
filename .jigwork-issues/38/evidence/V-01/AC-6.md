# 受入基準「秘密の扱い」(AC-6) 判定: 合格

## パスワードのハッシュだけ

- `jig gate` で「利用者の表はハッシュだけ」(TC-09) `backend/tests/test_i38_tc09_password_hash_only.py` が通った(argon2id のハッシュ、パスワードの列はハッシュだけ、DB のどこにも平文がない)。
- 移行 `backend/alembic/versions/0001_create_tables.py` の users の列は `password_hash` だけで、平文の列はない。

## 接続先とセッションの鍵は外から読み、無いと起動で止まる

- 検証役の手元で pytest を流し、「設定が無いと起動で止まる」(TC-10) `backend/tests/test_i38_tc10_startup_settings.py` の 12 件がすべて PASSED([pytest-local-sandbox.log](pytest-local-sandbox.log))。DATABASE_URL・SESSION_SECRET それぞれが無い・空・鍵が短いとき、サーバーは 0 でない終了コードで止まり、止まる理由に変数の名前が出て値は出ない。
- コード `backend/app/settings.py`: 環境変数と backend/.env(リポジトリに入れない)から読む。`backend/.env.example` は名前だけで値が 0 行(`git show HEAD:backend/.env.example` で値のある行を数えて 0)。追跡されている `.env` は `backend/.env.example` だけ。

## gitleaks の指摘 0 件(TC-22)

- コマンド: `gitleaks git --no-banner --redact`(8.30.1、リポジトリの直下で、`.gitleaks.toml` を使う)
- 出力の要点: `99 commits scanned.` `no leaks found`、終了コード 0。
- `.gitleaks.toml` の許可は、記録のファイル `.jigwork/records/issues/<番号>/log.jsonl` の中の `key":"<64 桁の 16 進>` の形だけ(人の答え Q-23)。製品のコードや文書への許可はない。

## 初期データのパスワード(要件 NFR-006・Q-08 の答え「環境変数から読む」)

- `jig gate` で「初期データのコマンド」(TC-11) `test_i38_tc11_seed_command.py` が通った: SEED_PASSWORD_EMPLOYEE / MANAGER / BUYER / ADMIN のどれかが無い・空だと止まる。
- 方式設計 `docs/internal/architecture.md` の「設定」「初期データ」の表と、`backend/.env.example` の変数名が一致。
