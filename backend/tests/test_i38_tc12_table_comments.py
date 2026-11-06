"""#38/TC-12: DB のカタログを引き、すべてのテーブルと列にコメントがあり、
テーブルのコメントが「T001 部署」の形である。移行を戻すと 5 つのテーブルが消える(NFR-011)。
"""

import re

import psycopg
from psycopg.rows import TupleRow

from tests.migrations import downgrade_base
from tests.postgres import PostgresServer

# alembic_version は道具の表なので、コメントの検査から外す(決定 D-06)
TOOL_TABLES = {"alembic_version"}

# 方式設計の「テーブル」の節の表
EXPECTED_TABLE_COMMENTS = {
    "departments": "T001 部署",
    "roles": "T002 役割",
    "users": "T003 利用者",
    "user_roles": "T004 利用者の役割",
    "sessions": "T005 ログインの状態",
}

TABLE_COMMENT_FORM = r"T\d{3} \S+"


def _table_comments(conn: psycopg.Connection[TupleRow]) -> dict[str, str | None]:
    rows = conn.execute(
        """
        SELECT c.relname, obj_description(c.oid, 'pg_class')
        FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p')
        """
    ).fetchall()
    return {str(name): None if comment is None else str(comment) for name, comment in rows if name not in TOOL_TABLES}


def test_i38_tc12_every_table_has_a_numbered_logical_name_comment(
    postgres_server: PostgresServer, migrated_database: str
) -> None:
    with psycopg.connect(postgres_server.conninfo(migrated_database)) as conn:
        comments = _table_comments(conn)

    assert comments == EXPECTED_TABLE_COMMENTS
    for table, comment in comments.items():
        assert comment is not None
        assert re.fullmatch(TABLE_COMMENT_FORM, comment), f"{table} のコメント「{comment}」が「T001 部署」の形でない"
    numbers = [comment.split(" ", 1)[0] for comment in comments.values() if comment is not None]
    assert len(set(numbers)) == len(numbers), "テーブル番号が重なっている"


def test_i38_tc12_every_column_has_a_logical_name_comment(
    postgres_server: PostgresServer, migrated_database: str
) -> None:
    with psycopg.connect(postgres_server.conninfo(migrated_database)) as conn:
        tables = set(_table_comments(conn))
        rows = conn.execute(
            """
            SELECT c.relname, a.attname, col_description(c.oid, a.attnum)
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            JOIN pg_attribute a ON a.attrelid = c.oid
            WHERE n.nspname = 'public' AND c.relkind IN ('r', 'p') AND a.attnum > 0 AND NOT a.attisdropped
            """
        ).fetchall()

    columns = [(str(table), str(column), comment) for table, column, comment in rows if table in tables]
    assert {table for table, _, _ in columns} == set(EXPECTED_TABLE_COMMENTS)
    missing = [f"{table}.{column}" for table, column, comment in columns if comment is None or not str(comment).strip()]
    assert missing == [], f"コメントの無い列がある: {missing}"


def test_i38_tc12_downgrade_removes_the_five_tables(postgres_server: PostgresServer, migrated_database: str) -> None:
    with psycopg.connect(postgres_server.conninfo(migrated_database)) as conn:
        before = set(_table_comments(conn))
    assert before == set(EXPECTED_TABLE_COMMENTS)

    downgrade_base(postgres_server.url(migrated_database))

    with psycopg.connect(postgres_server.conninfo(migrated_database)) as conn:
        after = set(_table_comments(conn))
    assert after == set()
