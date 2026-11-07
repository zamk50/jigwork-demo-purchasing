"""#38/TC-11: 初期データのコマンドを流し直しても、誤った回数とロックの終わる時刻を変えない(NFR-003・前提 A-26)。

流し直しは、氏名・部署・役割・パスワードを合わせるだけである。ログインの失敗で数えた回数とロックは残す。
"""

import secrets
from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import psycopg

from tests.api_client import api_client
from tests.apps import make_app, make_settings
from tests.clock import ManualClock
from tests.seeding import PASSWORD_VARIABLE_BY_EMPLOYEE_NO, SeededDatabase, run_seed

# 要件の値(FR-003)
MAX_FAILURES = 5
LOCK_DURATION = timedelta(minutes=15)

START = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
LOCKED_EMPLOYEE_NO = "000001"
NO_ROLE_EMPLOYEE_NO = "000003"
COUNTED_EMPLOYEE_NO = "000004"


def _lock_states(database_url: str) -> dict[str, tuple[int, datetime | None]]:
    conninfo = database_url.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(conninfo) as conn:
        rows = conn.execute("SELECT employee_no, failed_login_count, locked_until FROM users").fetchall()
    return {str(row[0]): (int(row[1]), row[2]) for row in rows}


def _remove_roles(database_url: str, employee_no: str) -> None:
    conninfo = database_url.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(conninfo) as conn:
        conn.execute(
            "DELETE FROM user_roles WHERE user_id = (SELECT id FROM users WHERE employee_no = %s)", (employee_no,)
        )


def _login(client: httpx.Client, employee_no: str, password: str) -> httpx.Response:
    return client.post("/api/auth/login", json={"employee_no": employee_no, "password": password})


def _reseed(seeded_database: SeededDatabase, cwd: Path) -> None:
    variables = {name: seeded_database.passwords[no] for no, name in PASSWORD_VARIABLE_BY_EMPLOYEE_NO.items()}
    result = run_seed(seeded_database.url, variables, cwd)
    assert result.returncode == 0, f"{result.stdout}\n{result.stderr}"


def test_i38_tc11_reseeding_keeps_the_failure_count_and_the_lock(
    seeded_database: SeededDatabase, tmp_path: Path
) -> None:
    _remove_roles(seeded_database.url, NO_ROLE_EMPLOYEE_NO)
    clock = ManualClock(START)
    app = make_app(make_settings(seeded_database.url), clock=clock)
    wrong = secrets.token_urlsafe(16)
    assert wrong not in seeded_database.passwords.values()

    with api_client(app) as client:
        for _ in range(MAX_FAILURES):
            assert _login(client, LOCKED_EMPLOYEE_NO, wrong).status_code == 401
        for _ in range(MAX_FAILURES - 1):
            assert _login(client, NO_ROLE_EMPLOYEE_NO, wrong).status_code == 401
        assert _login(client, NO_ROLE_EMPLOYEE_NO, seeded_database.passwords[NO_ROLE_EMPLOYEE_NO]).status_code == 401
        for _ in range(2):
            assert _login(client, COUNTED_EMPLOYEE_NO, wrong).status_code == 401

    before = _lock_states(seeded_database.url)
    assert before[LOCKED_EMPLOYEE_NO] == (MAX_FAILURES, START + LOCK_DURATION)
    assert before[NO_ROLE_EMPLOYEE_NO] == (MAX_FAILURES - 1, None)
    assert before[COUNTED_EMPLOYEE_NO] == (2, None)

    _reseed(seeded_database, tmp_path)

    assert _lock_states(seeded_database.url) == before

    # 流し直しで役割が戻った利用者は、残った回数のまま、正しいパスワードでログインできる
    with api_client(app) as client:
        restored = _login(client, NO_ROLE_EMPLOYEE_NO, seeded_database.passwords[NO_ROLE_EMPLOYEE_NO])
        still_locked = _login(client, LOCKED_EMPLOYEE_NO, seeded_database.passwords[LOCKED_EMPLOYEE_NO])

    assert restored.status_code == 200, restored.text
    assert still_locked.status_code == 401, still_locked.text
    after = _lock_states(seeded_database.url)
    assert after[NO_ROLE_EMPLOYEE_NO] == (0, None)
    assert after[LOCKED_EMPLOYEE_NO] == (MAX_FAILURES, START + LOCK_DURATION)
