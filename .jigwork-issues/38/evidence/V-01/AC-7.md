# 受入基準「テーブルの論理名」(AC-7) 判定: 合格

- 実行: `jig gate` で「DB のカタログを引くコメントの検査」(TC-12) `backend/tests/test_i38_tc12_table_comments.py` の 3 件が通った(失敗 0。[gate-run.json](gate-run.json))。
  - pg_class と obj_description で、public のテーブル(alembic_version を除く)のコメントが {departments: T001 部署, roles: T002 役割, users: T003 利用者, user_roles: T004 利用者の役割, sessions: T005 ログインの状態} と等しく、「T001 部署」の形で番号が重ならない。
  - pg_attribute と col_description で、5 つのテーブルの全列のコメントの欠けが 0 件。
  - downgrade base で 5 つのテーブルが消える。
- 突き合わせ: 方式設計 `docs/internal/architecture.md` の「テーブル」の節の表(T001〜T005 と列)と、移行 `backend/alembic/versions/0001_create_tables.py` のテーブル・列・コメントを 1 つずつ比べ、抜け・余分・食い違いはなかった(users の列 id〜updated_at の 9 列、sessions の 4 列ほか)。
