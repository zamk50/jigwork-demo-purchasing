"""#38/TC-09: 利用者の表にはパスワードのハッシュ(argon2id)だけがあり、平文はない(FR-010・NFR-005)。"""

from pathlib import Path

import psycopg
from argon2 import PasswordHasher
from psycopg import sql

from tests.postgres import PostgresServer
from tests.seeding import random_seed_passwords, run_seed

# 社員番号ごとのパスワードの環境変数(方式設計の「初期データ」の節)
PASSWORD_VARIABLE_BY_EMPLOYEE_NO = {
    "000001": "SEED_PASSWORD_EMPLOYEE",
    "000002": "SEED_PASSWORD_MANAGER",
    "000003": "SEED_PASSWORD_BUYER",
    "000004": "SEED_PASSWORD_ADMIN",
}


def _seed(postgres_server: PostgresServer, database: str, tmp_path: Path) -> dict[str, str]:
    passwords = random_seed_passwords()
    result = run_seed(postgres_server.url(database), passwords, tmp_path)
    assert result.returncode == 0, f"初期データのコマンドが失敗した:\n{result.stdout}\n{result.stderr}"
    return passwords


def test_i38_tc09_users_hold_argon2id_hash_of_each_password(
    postgres_server: PostgresServer, migrated_database: str, tmp_path: Path
) -> None:
    passwords = _seed(postgres_server, migrated_database, tmp_path)
    with psycopg.connect(postgres_server.conninfo(migrated_database)) as conn:
        rows = conn.execute("SELECT employee_no, password_hash FROM users ORDER BY employee_no").fetchall()

    assert [row[0] for row in rows] == sorted(PASSWORD_VARIABLE_BY_EMPLOYEE_NO)
    hasher = PasswordHasher()
    for employee_no, password_hash in rows:
        password = passwords[PASSWORD_VARIABLE_BY_EMPLOYEE_NO[employee_no]]
        assert isinstance(password_hash, str)
        assert password_hash.startswith("$argon2id$"), f"{employee_no} のハッシュが argon2id でない"
        assert password_hash != password
        assert hasher.verify(password_hash, password)


def test_i38_tc09_users_have_no_password_column_but_the_hash(
    postgres_server: PostgresServer, migrated_database: str
) -> None:
    with psycopg.connect(postgres_server.conninfo(migrated_database)) as conn:
        rows = conn.execute(
            """
            SELECT column_name FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = 'users'
            """
        ).fetchall()
    columns = {row[0] for row in rows}

    assert "password_hash" in columns
    assert {c for c in columns if "pass" in c or "pw" in c} == {"password_hash"}


def test_i38_tc09_no_plaintext_password_anywhere_in_the_database(
    postgres_server: PostgresServer, migrated_database: str, tmp_path: Path
) -> None:
    passwords = _seed(postgres_server, migrated_database, tmp_path)
    with psycopg.connect(postgres_server.conninfo(migrated_database)) as conn:
        tables = [
            row[0] for row in conn.execute("SELECT tablename FROM pg_tables WHERE schemaname = 'public'").fetchall()
        ]
        assert "users" in tables
        texts: list[str] = []
        for table in tables:
            query = sql.SQL("SELECT t::text FROM {} AS t").format(sql.Identifier(table))
            texts.extend(str(row[0]) for row in conn.execute(query).fetchall())

    for name, password in passwords.items():
        assert all(password not in text for text in texts), f"{name} の平文が DB にある"
