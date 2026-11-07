"""#38/TC-03: 同時に送った誤ったパスワードも、数え落とさずに数えてロックする(FR-003・決定 D-08)。

誤ったパスワードの要求を、スレッドごとに別のクライアントから同時に送る。要求ごとに別の DB の接続になる。
利用者の行を押さえずに数えると、同時の要求が同じ回数を読んで同じ値を書くので、回数が 5 に届かずロックしない。
"""

import secrets
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import UTC, datetime, timedelta

import httpx
import psycopg
from fastapi import FastAPI

from tests.api_client import api_client
from tests.apps import make_app, make_settings
from tests.clock import ManualClock
from tests.seeding import SeededDatabase

# 方式設計の「認証と認可の方式」の失敗の扱いの文
LOGIN_FAILED_MESSAGE = "社員番号かパスワードが違います"

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


def _login_together(app: FastAPI, employee_no: str, password: str, times: int) -> list[httpx.Response]:
    """times 本のスレッドで、そろって同時にログインの要求を送る。スレッドごとに別のクライアントを使う。"""
    barrier = threading.Barrier(times)

    def attempt() -> httpx.Response:
        client = api_client(app)
        try:
            barrier.wait(timeout=60)
            return client.post("/api/auth/login", json={"employee_no": employee_no, "password": password})
        finally:
            client.close()

    with ThreadPoolExecutor(max_workers=times) as pool:
        futures = [pool.submit(attempt) for _ in range(times)]
        return [future.result(timeout=120) for future in futures]


def test_i38_tc03_concurrent_failures_are_all_counted_and_lock(seeded_database: SeededDatabase) -> None:
    clock = ManualClock(START)
    app = make_app(make_settings(seeded_database.url), clock=clock)
    password = seeded_database.passwords[EMPLOYEE_NO]
    wrong = secrets.token_urlsafe(16)
    assert wrong not in seeded_database.passwords.values()

    with api_client(app) as client:
        responses = _login_together(app, EMPLOYEE_NO, wrong, MAX_FAILURES)
        for response in responses:
            assert response.status_code == 401, response.text
            assert response.json() == {"detail": LOGIN_FAILED_MESSAGE}

        assert _lock_state(seeded_database.url, EMPLOYEE_NO) == (MAX_FAILURES, START + LOCK_DURATION)

        # ロックしたので、正しいパスワードでもログインできない
        locked = client.post("/api/auth/login", json={"employee_no": EMPLOYEE_NO, "password": password})

    assert locked.status_code == 401, locked.text
    assert locked.json() == {"detail": LOGIN_FAILED_MESSAGE}


def test_i38_tc03_concurrent_failures_beyond_the_limit_stop_at_the_lock(seeded_database: SeededDatabase) -> None:
    clock = ManualClock(START)
    app = make_app(make_settings(seeded_database.url), clock=clock)
    wrong = secrets.token_urlsafe(16)
    assert wrong not in seeded_database.passwords.values()

    with api_client(app):
        responses = _login_together(app, EMPLOYEE_NO, wrong, MAX_FAILURES + 3)

    for response in responses:
        assert response.status_code == 401, response.text
        assert response.json() == {"detail": LOGIN_FAILED_MESSAGE}
    # 5 回目でロックし、その後の同時の試みはロック中として数えない
    assert _lock_state(seeded_database.url, EMPLOYEE_NO) == (MAX_FAILURES, START + LOCK_DURATION)
