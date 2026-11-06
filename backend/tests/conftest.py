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

from tests.postgres import PostgresServer

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
