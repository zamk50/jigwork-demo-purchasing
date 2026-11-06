"""#38/TC-08: 操作のない 30 分超と、ログインから 8 時間超で 401 になり、行が消える。
2 つのブラウザの同時のログインがどちらも有効である(FR-005・FR-006・FR-022)。

時刻はテストで進める時計で動かす。要件は「30 分を超える」「8 時間を超える」なので、
ちょうどの時刻ではまだ有効で、1 秒でも超えれば切れることを確かめる。

メニューの API はタスク T-6 で作るので、それまではログイン中の利用者の API で確かめる。
"""

from datetime import UTC, datetime, timedelta

import httpx
import psycopg

from tests.api_client import api_client
from tests.apps import make_app, make_settings
from tests.clock import ManualClock
from tests.seeding import SeededDatabase

# 要件の値(FR-005・FR-006)
IDLE_TIMEOUT = timedelta(minutes=30)
ABSOLUTE_TIMEOUT = timedelta(hours=8)
ONE_SECOND = timedelta(seconds=1)

START = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)


def _sessions(database_url: str) -> list[str]:
    """ログインの状態の行の、利用者の社員番号の一覧。"""
    conninfo = database_url.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(conninfo) as conn:
        rows = conn.execute(
            "SELECT u.employee_no FROM sessions s JOIN users u ON u.id = s.user_id ORDER BY u.employee_no"
        ).fetchall()
    return [str(row[0]) for row in rows]


def _login(client: httpx.Client, seeded_database: SeededDatabase, employee_no: str) -> None:
    response = client.post(
        "/api/auth/login", json={"employee_no": employee_no, "password": seeded_database.passwords[employee_no]}
    )
    assert response.status_code == 200, response.text


def test_i38_tc08_idle_for_more_than_30_minutes_is_401(seeded_database: SeededDatabase) -> None:
    clock = ManualClock(START)
    app = make_app(make_settings(seeded_database.url), clock=clock)

    with api_client(app) as client:
        _login(client, seeded_database, "000001")

        # ちょうど 30 分はまだ有効で、最後の操作の時刻がそこに進む
        clock.advance(IDLE_TIMEOUT)
        assert client.get("/api/me").status_code == 200

        clock.advance(IDLE_TIMEOUT + ONE_SECOND)
        expired = client.get("/api/me")
        assert expired.status_code == 401
        assert _sessions(seeded_database.url) == []

        # 行が消えたので、同じ印では二度と通らない
        assert client.get("/api/me").status_code == 401


def test_i38_tc08_more_than_8_hours_after_login_is_401_even_while_active(seeded_database: SeededDatabase) -> None:
    clock = ManualClock(START)
    app = make_app(make_settings(seeded_database.url), clock=clock)
    step = timedelta(minutes=20)
    assert step < IDLE_TIMEOUT

    with api_client(app) as client:
        _login(client, seeded_database, "000002")

        # 30 分を超えて操作が途切れないよう、20 分ごとに操作して 8 時間ちょうどまで進める
        while clock.now() + step <= START + ABSOLUTE_TIMEOUT:
            clock.advance(step)
            assert client.get("/api/me").status_code == 200, clock.now()
        assert clock.now() == START + ABSOLUTE_TIMEOUT

        clock.advance(ONE_SECOND)
        expired = client.get("/api/me")
        assert expired.status_code == 401
        assert _sessions(seeded_database.url) == []


def test_i38_tc08_two_browsers_can_be_logged_in_at_the_same_time(seeded_database: SeededDatabase) -> None:
    clock = ManualClock(START)
    app = make_app(make_settings(seeded_database.url), clock=clock)

    with api_client(app) as browser_a, api_client(app) as browser_b:
        _login(browser_a, seeded_database, "000001")
        clock.advance(timedelta(minutes=5))
        _login(browser_b, seeded_database, "000001")

        assert browser_a.get("/api/me").status_code == 200
        assert browser_b.get("/api/me").status_code == 200
        assert _sessions(seeded_database.url) == ["000001", "000001"]

        # 一方のログアウトは、もう一方のログインの状態を消さない
        assert browser_a.post("/api/auth/logout", json={}).status_code == 204
        assert browser_a.get("/api/me").status_code == 401
        assert browser_b.get("/api/me").status_code == 200
        assert _sessions(seeded_database.url) == ["000001"]


def test_i38_tc08_one_browser_timing_out_does_not_end_the_other(seeded_database: SeededDatabase) -> None:
    clock = ManualClock(START)
    app = make_app(make_settings(seeded_database.url), clock=clock)

    with api_client(app) as browser_a, api_client(app) as browser_b:
        _login(browser_a, seeded_database, "000001")
        _login(browser_b, seeded_database, "000001")

        clock.advance(timedelta(minutes=20))
        assert browser_b.get("/api/me").status_code == 200
        clock.advance(timedelta(minutes=20))

        assert browser_a.get("/api/me").status_code == 401
        assert browser_b.get("/api/me").status_code == 200
        assert _sessions(seeded_database.url) == ["000001"]


def test_i38_tc08_login_removes_expired_sessions_of_others(seeded_database: SeededDatabase) -> None:
    clock = ManualClock(START)
    app = make_app(make_settings(seeded_database.url), clock=clock)

    with api_client(app) as idle, api_client(app) as active, api_client(app) as later:
        _login(idle, seeded_database, "000001")
        _login(active, seeded_database, "000003")

        clock.advance(timedelta(minutes=20))
        assert active.get("/api/me").status_code == 200
        clock.advance(timedelta(minutes=20))
        assert _sessions(seeded_database.url) == ["000001", "000003"]

        # 期限の切れた 000001 の行は、ほかの利用者のログインでまとめて消える
        _login(later, seeded_database, "000004")
        assert _sessions(seeded_database.url) == ["000003", "000004"]
