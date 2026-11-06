"""差し替えられる時計と、要求ごとのトランザクション(方式設計の「横断の方式」の節)。

- 時計: アプリに渡した時計を口の依存から引ける。テストでは進める時計を渡す。
- トランザクション: 要求 1 つを 1 つにする。応答を返せば確定し、想定しない例外なら取り消す。
  想定した誤り(401 など)は応答として返すので、その前の書き込みも確定する。
"""

import secrets
from datetime import UTC, datetime, timedelta

import psycopg
from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.api.deps import CurrentClock, CurrentSettings, DbSession
from app.clock import Clock, SystemClock
from app.db.models import Department
from app.main import create_app
from app.settings import load_settings
from tests.api_client import api_client
from tests.clock import ManualClock
from tests.postgres import PostgresServer


def _app(database_url: str, clock: Clock | None = None) -> FastAPI:
    settings = load_settings({"DATABASE_URL": database_url, "SESSION_SECRET": secrets.token_urlsafe(32)})
    return create_app(settings, clock=clock)


def _department_count(postgres_server: PostgresServer, database: str, name: str) -> int:
    with psycopg.connect(postgres_server.conninfo(database)) as conn:
        row = conn.execute("SELECT count(*) FROM departments WHERE name = %s", (name,)).fetchone()
    assert row is not None
    return int(row[0])


def test_system_clock_returns_the_current_utc_time() -> None:
    before = datetime.now(UTC)
    now = SystemClock().now()
    after = datetime.now(UTC)

    assert now.utcoffset() == timedelta(0)
    assert before <= now <= after


def test_app_uses_the_given_clock(postgres_server: PostgresServer) -> None:
    clock = ManualClock(datetime(2026, 4, 1, 9, 0, tzinfo=UTC))
    app = _app(postgres_server.url(), clock=clock)

    def now_route(current: CurrentClock) -> dict[str, str]:
        return {"now": current.now().isoformat()}

    app.add_api_route("/test/now", now_route, methods=["GET"])

    with api_client(app) as client:
        first = client.get("/test/now").json()["now"]
        clock.advance(timedelta(minutes=30))
        second = client.get("/test/now").json()["now"]
        clock.advance(timedelta(hours=8))
        third = client.get("/test/now").json()["now"]

    assert datetime.fromisoformat(first) == datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
    assert datetime.fromisoformat(second) == datetime(2026, 4, 1, 9, 30, tzinfo=UTC)
    assert datetime.fromisoformat(third) == datetime(2026, 4, 1, 17, 30, tzinfo=UTC)


def test_app_without_a_clock_uses_the_system_clock(postgres_server: PostgresServer) -> None:
    app = _app(postgres_server.url())

    def now_route(current: CurrentClock) -> dict[str, str]:
        return {"now": current.now().isoformat()}

    app.add_api_route("/test/now", now_route, methods=["GET"])

    before = datetime.now(UTC)
    with api_client(app) as client:
        now = datetime.fromisoformat(client.get("/test/now").json()["now"])
    after = datetime.now(UTC)

    assert before <= now <= after


def test_app_exposes_its_settings(postgres_server: PostgresServer) -> None:
    app = _app(postgres_server.url())

    def settings_route(settings: CurrentSettings) -> dict[str, bool]:
        return {"cookie_secure": settings.cookie_secure}

    app.add_api_route("/test/settings", settings_route, methods=["GET"])

    with api_client(app) as client:
        assert client.get("/test/settings").json() == {"cookie_secure": True}


def test_request_commits_when_a_response_is_returned(postgres_server: PostgresServer, migrated_database: str) -> None:
    name = f"確定する部{secrets.token_hex(3)}"
    app = _app(postgres_server.url(migrated_database))

    def write_route(db: DbSession) -> dict[str, str]:
        db.add(Department(name=name))
        return {"status": "ok"}

    app.add_api_route("/test/write", write_route, methods=["POST"])

    with api_client(app) as client:
        response = client.post("/test/write")

    assert response.status_code == 200
    assert _department_count(postgres_server, migrated_database, name) == 1


def test_request_commits_before_an_expected_error_response(
    postgres_server: PostgresServer, migrated_database: str
) -> None:
    name = f"誤りでも確定する部{secrets.token_hex(3)}"
    app = _app(postgres_server.url(migrated_database))

    def expected_error_route(db: DbSession) -> JSONResponse:
        db.add(Department(name=name))
        return JSONResponse(status_code=401, content={"detail": "想定した誤り"})

    app.add_api_route("/test/expected-error", expected_error_route, methods=["POST"])

    with api_client(app) as client:
        response = client.post("/test/expected-error")

    assert response.status_code == 401
    assert _department_count(postgres_server, migrated_database, name) == 1


def test_request_rolls_back_on_an_unexpected_exception(postgres_server: PostgresServer, migrated_database: str) -> None:
    name = f"取り消す部{secrets.token_hex(3)}"
    app = _app(postgres_server.url(migrated_database))

    def failing_route(db: DbSession) -> dict[str, str]:
        db.add(Department(name=name))
        db.flush()
        raise RuntimeError("想定しない例外")

    app.add_api_route("/test/fail", failing_route, methods=["POST"])

    with api_client(app, raise_server_exceptions=False) as client:
        response = client.post("/test/fail")

    assert response.status_code == 500
    assert _department_count(postgres_server, migrated_database, name) == 0
