"""#38/TC-11: 初期データのコマンドは、パスワードの環境変数が無いと止まる。
流すと 4 利用者の行が入り、2 回流しても同じ結果である(NFR-003・NFR-006)。
"""

from pathlib import Path
from typing import Any

import psycopg
import pytest
from argon2 import PasswordHasher

from tests.postgres import PostgresServer
from tests.seeding import SEED_PASSWORD_VARIABLES, random_seed_passwords, run_seed

# 方式設計の「初期データ」の節の表: 社員番号・氏名・部署・役割(並び順)
EXPECTED_USERS = [
    ("000001", "社員 一郎", "営業部", ["employee"]),
    ("000002", "上長 二郎", "営業部", ["employee", "manager"]),
    ("000003", "購買 三子", "総務部", ["buyer"]),
    ("000004", "管理 四郎", "総務部", ["admin"]),
]


def _users(postgres_server: PostgresServer, database: str) -> list[tuple[Any, ...]]:
    with psycopg.connect(postgres_server.conninfo(database)) as conn:
        return conn.execute(
            """
            SELECT u.employee_no, u.name, d.name,
                   array(SELECT ur.role_code FROM user_roles ur JOIN roles r ON r.code = ur.role_code
                         WHERE ur.user_id = u.id ORDER BY r.sort_order)
            FROM users u JOIN departments d ON d.id = u.department_id
            ORDER BY u.employee_no
            """
        ).fetchall()


def _snapshot(postgres_server: PostgresServer, database: str) -> tuple[list[tuple[Any, ...]], ...]:
    with psycopg.connect(postgres_server.conninfo(database)) as conn:
        users = conn.execute("SELECT * FROM users ORDER BY id").fetchall()
        user_roles = conn.execute("SELECT * FROM user_roles ORDER BY user_id, role_code").fetchall()
        departments = conn.execute("SELECT * FROM departments ORDER BY id").fetchall()
        roles = conn.execute("SELECT * FROM roles ORDER BY code").fetchall()
    return users, user_roles, departments, roles


def _user_count(postgres_server: PostgresServer, database: str) -> int:
    with psycopg.connect(postgres_server.conninfo(database)) as conn:
        row = conn.execute("SELECT count(*) FROM users").fetchone()
    assert row is not None
    return int(row[0])


@pytest.mark.parametrize("missing", SEED_PASSWORD_VARIABLES)
def test_i38_tc11_seed_stops_without_a_password_variable(
    postgres_server: PostgresServer, migrated_database: str, tmp_path: Path, missing: str
) -> None:
    passwords = random_seed_passwords()
    del passwords[missing]

    result = run_seed(postgres_server.url(migrated_database), passwords, tmp_path)

    assert result.returncode != 0
    assert missing in result.stderr, f"止まった理由に {missing} が出ていない:\n{result.stderr}"
    output = f"{result.stdout}\n{result.stderr}"
    assert all(password not in output for password in passwords.values()), "パスワードが出力に出ている"
    assert _user_count(postgres_server, migrated_database) == 0


@pytest.mark.parametrize("empty", SEED_PASSWORD_VARIABLES)
def test_i38_tc11_seed_stops_with_an_empty_password_variable(
    postgres_server: PostgresServer, migrated_database: str, tmp_path: Path, empty: str
) -> None:
    passwords = random_seed_passwords()
    passwords[empty] = ""

    result = run_seed(postgres_server.url(migrated_database), passwords, tmp_path)

    assert result.returncode != 0
    assert empty in result.stderr, f"止まった理由に {empty} が出ていない:\n{result.stderr}"
    assert _user_count(postgres_server, migrated_database) == 0


def test_i38_tc11_seed_inserts_four_users_and_twice_gives_the_same_result(
    postgres_server: PostgresServer, migrated_database: str, tmp_path: Path
) -> None:
    url = postgres_server.url(migrated_database)
    passwords = random_seed_passwords()

    first = run_seed(url, passwords, tmp_path)
    assert first.returncode == 0, f"1 回目が失敗した:\n{first.stdout}\n{first.stderr}"
    assert _users(postgres_server, migrated_database) == [
        (no, name, dept, roles) for no, name, dept, roles in EXPECTED_USERS
    ]
    after_first = _snapshot(postgres_server, migrated_database)

    second = run_seed(url, passwords, tmp_path)
    assert second.returncode == 0, f"2 回目が失敗した:\n{second.stdout}\n{second.stderr}"
    assert _snapshot(postgres_server, migrated_database) == after_first


def test_i38_tc11_seed_restores_name_department_roles_and_password(
    postgres_server: PostgresServer, migrated_database: str, tmp_path: Path
) -> None:
    url = postgres_server.url(migrated_database)
    passwords = random_seed_passwords()
    first = run_seed(url, passwords, tmp_path)
    assert first.returncode == 0, f"1 回目が失敗した:\n{first.stdout}\n{first.stderr}"
    with psycopg.connect(postgres_server.conninfo(migrated_database)) as conn:
        id_row = conn.execute("SELECT id FROM users WHERE employee_no = '000002'").fetchone()
        assert id_row is not None
        user_id = id_row[0]
        conn.execute("UPDATE users SET name = '別の名前' WHERE id = %s", (user_id,))
        conn.execute(
            "UPDATE users SET department_id = (SELECT id FROM departments WHERE name = '製造部') WHERE id = %s",
            (user_id,),
        )
        conn.execute("DELETE FROM user_roles WHERE user_id = %s AND role_code = 'manager'", (user_id,))
        conn.execute("INSERT INTO user_roles (user_id, role_code) VALUES (%s, 'admin')", (user_id,))

    passwords["SEED_PASSWORD_MANAGER"] = random_seed_passwords()["SEED_PASSWORD_MANAGER"]
    second = run_seed(url, passwords, tmp_path)
    assert second.returncode == 0, f"2 回目が失敗した:\n{second.stdout}\n{second.stderr}"

    assert _users(postgres_server, migrated_database) == [
        (no, name, dept, roles) for no, name, dept, roles in EXPECTED_USERS
    ]
    with psycopg.connect(postgres_server.conninfo(migrated_database)) as conn:
        row = conn.execute("SELECT id, password_hash FROM users WHERE employee_no = '000002'").fetchone()
    assert row is not None
    assert row[0] == user_id, "利用者を作り直さず、同じ行を直す"
    assert PasswordHasher().verify(row[1], passwords["SEED_PASSWORD_MANAGER"])
