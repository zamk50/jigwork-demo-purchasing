"""テストの土台: 一時の PostgreSQL を立てる fixture。

常駐の PostgreSQL のサービスは使わない。一時ディレクトリにクラスタを作り、
unix ソケットだけで待ち受け、テストが終われば止めて消す。
"""

import shutil
import subprocess
import tempfile
import uuid
from collections.abc import Iterator
from pathlib import Path

import psycopg
import pytest
from psycopg import sql

from tests.migrations import upgrade_head
from tests.postgres import PostgresServer
from tests.seeding import PASSWORD_VARIABLE_BY_EMPLOYEE_NO, SeededDatabase, random_seed_passwords, run_seed

PG_BIN = Path("/usr/lib/postgresql/18/bin")
PG_USER = "postgres"
PG_PORT = 5432


def _run(args: list[str]) -> None:
    result = subprocess.run(args, capture_output=True, text=True, check=False)
    if result.returncode != 0:
        detail = f"{result.stdout}\n{result.stderr}"
        raise RuntimeError(f"{args[0]} が失敗した(終了コード {result.returncode}):\n{detail}")


@pytest.fixture(scope="session")
def postgres_server() -> Iterator[PostgresServer]:
    """一時ディレクトリに PostgreSQL 18 を立て、テストの全体が終われば止めて消す。"""
    base = Path(tempfile.mkdtemp(prefix="pg-"))
    data = base / "data"
    server = PostgresServer(base_dir=base, data_dir=data, socket_dir=base, port=PG_PORT, user=PG_USER)
    started = False
    try:
        _run(
            [
                str(PG_BIN / "initdb"),
                "-D",
                str(data),
                "-U",
                PG_USER,
                "-A",
                "trust",
                "-E",
                "UTF8",
                "--no-locale",
                "--no-sync",
            ]
        )
        options = f"-c listen_addresses='' -k {base} -p {PG_PORT} -c fsync=off"
        log = base / "server.log"
        try:
            _run([str(PG_BIN / "pg_ctl"), "-D", str(data), "-l", str(log), "-o", options, "-w", "start"])
        except RuntimeError as e:
            text = log.read_text(errors="replace") if log.exists() else ""
            raise RuntimeError(f"{e}\nサーバーのログ:\n{text}") from e
        started = True
        yield server
    finally:
        if started:
            _run([str(PG_BIN / "pg_ctl"), "-D", str(data), "-m", "immediate", "-w", "stop"])
        shutil.rmtree(base, ignore_errors=True)


@pytest.fixture
def postgres_database(postgres_server: PostgresServer) -> Iterator[str]:
    """テストごとに空のデータベースを作り、その名前を返す。終われば消す。"""
    name = f"t_{uuid.uuid4().hex}"
    with psycopg.connect(postgres_server.conninfo(), autocommit=True) as conn:
        conn.execute(sql.SQL("CREATE DATABASE {}").format(sql.Identifier(name)))
    try:
        yield name
    finally:
        with psycopg.connect(postgres_server.conninfo(), autocommit=True) as conn:
            conn.execute(sql.SQL("DROP DATABASE IF EXISTS {} WITH (FORCE)").format(sql.Identifier(name)))


@pytest.fixture
def migrated_database(postgres_server: PostgresServer, postgres_database: str) -> str:
    """空のデータベースに移行を最後まで流し、その名前を返す。"""
    upgrade_head(postgres_server.url(postgres_database))
    return postgres_database


@pytest.fixture
def seeded_database(postgres_server: PostgresServer, migrated_database: str, tmp_path: Path) -> SeededDatabase:
    """移行と初期データのコマンドだけで入れた DB。パスワードはそのたびに作る乱数にする。"""
    url = postgres_server.url(migrated_database)
    variables = random_seed_passwords()
    result = run_seed(url, variables, tmp_path)
    if result.returncode != 0:
        raise RuntimeError(f"初期データのコマンドが失敗した:\n{result.stdout}\n{result.stderr}")
    passwords = {no: variables[name] for no, name in PASSWORD_VARIABLE_BY_EMPLOYEE_NO.items()}
    return SeededDatabase(url=url, passwords=passwords)
