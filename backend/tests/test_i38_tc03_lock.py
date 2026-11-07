"""#38/TC-03: 5 回の誤りで 15 分ロックし、過ぎればログインできる。ロック明けの 1 回の誤りではロックしない。
4 回誤って成功した後、4 回誤ってもロックしない。ロック中の試みは数えない(FR-003・FR-004・FR-020)。

時刻はテストで進める時計で動かす。ロックの境目は、要件の「15 分ロック」に合わせ、
ロックした時刻から 15 分の手前ではロック中、15 分を過ぎればロック明けとして確かめる。
"""

import secrets
from datetime import UTC, datetime, timedelta

import httpx
import psycopg

from tests.api_client import api_client
from tests.apps import make_app, make_settings
from tests.clock import ManualClock
from tests.seeding import SeededDatabase

# 方式設計の「認証と認可の方式」の失敗の扱いの文
LOGIN_FAILED_MESSAGE = "社員番号かパスワードが違います"

# 要件の値(FR-003)
MAX_FAILURES = 5
LOCK_DURATION = timedelta(minutes=15)
ONE_SECOND = timedelta(seconds=1)

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


def _wrong_password(seeded_database: SeededDatabase) -> str:
    wrong = secrets.token_urlsafe(16)
    assert wrong not in seeded_database.passwords.values()
    return wrong


def _assert_failed(response: httpx.Response) -> None:
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": LOGIN_FAILED_MESSAGE}


def _fail_times(client: httpx.Client, password: str, times: int) -> None:
    for _ in range(times):
        _assert_failed(_login(client, EMPLOYEE_NO, password))


def test_i38_tc03_five_failures_lock_for_15_minutes(seeded_database: SeededDatabase) -> None:
    clock = ManualClock(START)
    app = make_app(make_settings(seeded_database.url), clock=clock)
    password = seeded_database.passwords[EMPLOYEE_NO]
    wrong = _wrong_password(seeded_database)

    with api_client(app) as client:
        _fail_times(client, wrong, MAX_FAILURES - 1)
        assert _lock_state(seeded_database.url, EMPLOYEE_NO) == (MAX_FAILURES - 1, None)

        _fail_times(client, wrong, 1)
        assert _lock_state(seeded_database.url, EMPLOYEE_NO) == (MAX_FAILURES, START + LOCK_DURATION)

        # ロック中は正しいパスワードでもログインできず、文は誤ったパスワードと同じである
        locked = _login(client, EMPLOYEE_NO, password)
        _assert_failed(locked)
        assert "session" not in dict(client.cookies)

        clock.advance(LOCK_DURATION - ONE_SECOND)
        _assert_failed(_login(client, EMPLOYEE_NO, password))

        clock.advance(2 * ONE_SECOND)
        unlocked = _login(client, EMPLOYEE_NO, password)
        assert unlocked.status_code == 200, unlocked.text
        assert unlocked.json()["employee_no"] == EMPLOYEE_NO

    assert _lock_state(seeded_database.url, EMPLOYEE_NO) == (0, None)


def test_i38_tc03_lock_is_per_user(seeded_database: SeededDatabase) -> None:
    clock = ManualClock(START)
    app = make_app(make_settings(seeded_database.url), clock=clock)
    wrong = _wrong_password(seeded_database)

    with api_client(app) as client:
        _fail_times(client, wrong, MAX_FAILURES)
        other = _login(client, "000004", seeded_database.passwords["000004"])

    assert other.status_code == 200, other.text
    assert _lock_state(seeded_database.url, "000004") == (0, None)


def test_i38_tc03_one_failure_after_the_lock_ends_does_not_lock(seeded_database: SeededDatabase) -> None:
    clock = ManualClock(START)
    app = make_app(make_settings(seeded_database.url), clock=clock)
    password = seeded_database.passwords[EMPLOYEE_NO]
    wrong = _wrong_password(seeded_database)

    with api_client(app) as client:
        _fail_times(client, wrong, MAX_FAILURES)
        clock.advance(LOCK_DURATION + ONE_SECOND)

        # ロック明けの最初の誤りで回数は 0 から数え直す
        _fail_times(client, wrong, 1)
        assert _lock_state(seeded_database.url, EMPLOYEE_NO) == (1, None)

        # 続けて 3 回誤っても 4 回目なのでロックしない
        _fail_times(client, wrong, MAX_FAILURES - 2)
        assert _lock_state(seeded_database.url, EMPLOYEE_NO) == (MAX_FAILURES - 1, None)

        success = _login(client, EMPLOYEE_NO, password)

    assert success.status_code == 200, success.text
    assert _lock_state(seeded_database.url, EMPLOYEE_NO) == (0, None)


def test_i38_tc03_the_fifth_failure_after_the_lock_ends_locks_again(seeded_database: SeededDatabase) -> None:
    clock = ManualClock(START)
    app = make_app(make_settings(seeded_database.url), clock=clock)
    password = seeded_database.passwords[EMPLOYEE_NO]
    wrong = _wrong_password(seeded_database)

    with api_client(app) as client:
        _fail_times(client, wrong, MAX_FAILURES)
        clock.advance(LOCK_DURATION + ONE_SECOND)
        relock_at = clock.now()

        _fail_times(client, wrong, MAX_FAILURES)
        assert _lock_state(seeded_database.url, EMPLOYEE_NO) == (MAX_FAILURES, relock_at + LOCK_DURATION)
        _assert_failed(_login(client, EMPLOYEE_NO, password))


def test_i38_tc03_success_resets_the_count(seeded_database: SeededDatabase) -> None:
    clock = ManualClock(START)
    app = make_app(make_settings(seeded_database.url), clock=clock)
    password = seeded_database.passwords[EMPLOYEE_NO]
    wrong = _wrong_password(seeded_database)

    with api_client(app) as client:
        _fail_times(client, wrong, MAX_FAILURES - 1)
        first = _login(client, EMPLOYEE_NO, password)
        assert first.status_code == 200, first.text
        assert _lock_state(seeded_database.url, EMPLOYEE_NO) == (0, None)
        assert client.post("/api/auth/logout", json={}).status_code == 204

        _fail_times(client, wrong, MAX_FAILURES - 1)
        assert _lock_state(seeded_database.url, EMPLOYEE_NO) == (MAX_FAILURES - 1, None)
        second = _login(client, EMPLOYEE_NO, password)

    assert second.status_code == 200, second.text


def test_i38_tc03_attempts_while_locked_are_not_counted(seeded_database: SeededDatabase) -> None:
    clock = ManualClock(START)
    app = make_app(make_settings(seeded_database.url), clock=clock)
    password = seeded_database.passwords[EMPLOYEE_NO]
    wrong = _wrong_password(seeded_database)

    with api_client(app) as client:
        _fail_times(client, wrong, MAX_FAILURES)
        locked_state = _lock_state(seeded_database.url, EMPLOYEE_NO)
        assert locked_state == (MAX_FAILURES, START + LOCK_DURATION)

        # ロック中の誤りと正しいパスワードの試みは、回数にもロックの終わる時刻にも効かない
        clock.advance(timedelta(minutes=5))
        _fail_times(client, wrong, 3)
        _assert_failed(_login(client, EMPLOYEE_NO, password))
        clock.advance(timedelta(minutes=9))
        _fail_times(client, wrong, 1)
        assert _lock_state(seeded_database.url, EMPLOYEE_NO) == locked_state

        clock.advance(timedelta(minutes=1) + ONE_SECOND)
        assert clock.now() == START + LOCK_DURATION + ONE_SECOND
        success = _login(client, EMPLOYEE_NO, password)

    assert success.status_code == 200, success.text
    assert _lock_state(seeded_database.url, EMPLOYEE_NO) == (0, None)


def test_i38_tc03_unknown_employee_no_is_never_locked(seeded_database: SeededDatabase) -> None:
    clock = ManualClock(START)
    app = make_app(make_settings(seeded_database.url), clock=clock)
    wrong = _wrong_password(seeded_database)

    with api_client(app) as client:
        for _ in range(MAX_FAILURES + 1):
            _assert_failed(_login(client, "999999", wrong))

    for employee_no in seeded_database.passwords:
        assert _lock_state(seeded_database.url, employee_no) == (0, None)
