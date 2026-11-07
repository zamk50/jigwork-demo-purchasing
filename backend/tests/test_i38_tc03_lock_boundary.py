"""#38/TC-03: ロックの終わる時刻ちょうどの試みは受ける(FR-004。方式設計の「認証と認可の方式」のロック・前提 A-18)。

ロックした時刻からちょうど 15 分で、正しいパスワードならログインでき、回数は 0 に戻る。
"""

import secrets
from datetime import UTC, datetime, timedelta

import httpx
import psycopg

from tests.api_client import api_client
from tests.apps import make_app, make_settings
from tests.clock import ManualClock
from tests.seeding import SeededDatabase

# 要件の値(FR-003)
MAX_FAILURES = 5
LOCK_DURATION = timedelta(minutes=15)

START = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
EMPLOYEE_NO = "000001"


def _lock_state(database_url: str, employee_no: str) -> tuple[int, datetime | None]:
    conninfo = database_url.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(conninfo) as conn:
        row = conn.execute(
            "SELECT failed_login_count, locked_until FROM users WHERE employee_no = %s", (employee_no,)
        ).fetchone()
    assert row is not None
    return int(row[0]), row[1]


def _login(client: httpx.Client, employee_no: str, password: str) -> httpx.Response:
    return client.post("/api/auth/login", json={"employee_no": employee_no, "password": password})


def test_i38_tc03_login_at_exactly_the_lock_end_is_accepted(seeded_database: SeededDatabase) -> None:
    clock = ManualClock(START)
    app = make_app(make_settings(seeded_database.url), clock=clock)
    password = seeded_database.passwords[EMPLOYEE_NO]
    wrong = secrets.token_urlsafe(16)
    assert wrong not in seeded_database.passwords.values()

    with api_client(app) as client:
        for _ in range(MAX_FAILURES):
            assert _login(client, EMPLOYEE_NO, wrong).status_code == 401
        assert _lock_state(seeded_database.url, EMPLOYEE_NO) == (MAX_FAILURES, START + LOCK_DURATION)

        clock.advance(LOCK_DURATION)
        assert clock.now() == START + LOCK_DURATION
        response = _login(client, EMPLOYEE_NO, password)

    assert response.status_code == 200, response.text
    assert response.json()["employee_no"] == EMPLOYEE_NO
    assert _lock_state(seeded_database.url, EMPLOYEE_NO) == (0, None)
