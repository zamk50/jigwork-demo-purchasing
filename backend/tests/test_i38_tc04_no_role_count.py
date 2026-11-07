"""#38/TC-04: 役割なしの利用者が正しいパスワードを入れても、誤った回数を変えない(FR-003・FR-023・前提 A-19)。

役割なしの利用者は、正しいパスワードでも 401 である。誤りでも成功でもないので、回数を 0 に戻さず、足しもしない。
"""

import secrets
from datetime import datetime

import httpx
import psycopg

from tests.api_client import api_client
from tests.apps import make_app, make_settings
from tests.seeding import SeededDatabase

# 方式設計の「認証と認可の方式」の失敗の扱いの文
LOGIN_FAILED_MESSAGE = "社員番号かパスワードが違います"

# 要件の値(FR-003)
MAX_FAILURES = 5

EMPLOYEE_NO = "000003"


def _lock_state(database_url: str, employee_no: str) -> tuple[int, datetime | None]:
    conninfo = database_url.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(conninfo) as conn:
        row = conn.execute(
            "SELECT failed_login_count, locked_until FROM users WHERE employee_no = %s", (employee_no,)
        ).fetchone()
    assert row is not None
    return int(row[0]), row[1]


def _remove_roles(database_url: str, employee_no: str) -> None:
    conninfo = database_url.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(conninfo) as conn:
        conn.execute(
            "DELETE FROM user_roles WHERE user_id = (SELECT id FROM users WHERE employee_no = %s)", (employee_no,)
        )


def _login(client: httpx.Client, employee_no: str, password: str) -> httpx.Response:
    return client.post("/api/auth/login", json={"employee_no": employee_no, "password": password})


def _assert_failed(response: httpx.Response) -> None:
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": LOGIN_FAILED_MESSAGE}


def test_i38_tc04_correct_password_without_roles_keeps_the_count(seeded_database: SeededDatabase) -> None:
    _remove_roles(seeded_database.url, EMPLOYEE_NO)
    app = make_app(make_settings(seeded_database.url))
    password = seeded_database.passwords[EMPLOYEE_NO]
    wrong = secrets.token_urlsafe(16)
    assert wrong not in seeded_database.passwords.values()

    with api_client(app) as client:
        for _ in range(MAX_FAILURES - 1):
            _assert_failed(_login(client, EMPLOYEE_NO, wrong))
        assert _lock_state(seeded_database.url, EMPLOYEE_NO) == (MAX_FAILURES - 1, None)

        _assert_failed(_login(client, EMPLOYEE_NO, password))
        assert _lock_state(seeded_database.url, EMPLOYEE_NO) == (MAX_FAILURES - 1, None)

        # 回数が残っているので、次の 1 回の誤りでロックする
        _assert_failed(_login(client, EMPLOYEE_NO, wrong))

    count, locked_until = _lock_state(seeded_database.url, EMPLOYEE_NO)
    assert count == MAX_FAILURES
    assert locked_until is not None
