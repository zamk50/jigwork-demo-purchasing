"""テストの土台の一時の PostgreSQL が、決めたとおりに立つことを確かめる。"""

import tempfile
from pathlib import Path

import psycopg

from tests.postgres import PostgresServer


def test_postgres_server_runs_version_18_in_a_temporary_directory(postgres_server: PostgresServer) -> None:
    assert postgres_server.data_dir.is_relative_to(Path(tempfile.gettempdir()))
    with psycopg.connect(postgres_server.conninfo()) as conn:
        row = conn.execute("SELECT current_setting('server_version_num')::int").fetchone()
    assert row is not None
    assert row[0] // 10000 == 18


def test_postgres_database_is_empty_and_writable(postgres_server: PostgresServer, postgres_database: str) -> None:
    with psycopg.connect(postgres_server.conninfo(postgres_database)) as conn:
        tables = conn.execute("SELECT count(*) FROM pg_tables WHERE schemaname = 'public'").fetchone()
        conn.execute("CREATE TABLE probe (id integer PRIMARY KEY)")
        conn.execute("INSERT INTO probe (id) VALUES (1)")
        count = conn.execute("SELECT count(*) FROM probe").fetchone()
    assert tables == (0,)
    assert count == (1,)
