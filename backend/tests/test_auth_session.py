"""ログインの状態の持ち方(決定 D-01。方式設計の「認証と認可の方式」)。

- 表に入れるのは印そのものではなく、鍵 SESSION_SECRET による HMAC-SHA256 である。
- 印はクッキー session で返す。HttpOnly・SameSite=Lax・Path=/ で、設定により Secure も付ける。
- ログインとログイン中の利用者の API で、ログインした時刻と最後の操作の時刻をアプリの時計で持つ。
- ログイン・ログアウトは JSON の要求だけを受ける(要求の偽造への備え)。
- ログにはログインの成否と社員番号を残し、パスワードと印は残さない。
"""

import hashlib
import hmac
import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Any

import psycopg
import pytest

from tests.api_client import api_client
from tests.apps import make_app, make_settings
from tests.clock import ManualClock
from tests.seeding import SeededDatabase


def _sessions(database_url: str) -> list[tuple[Any, ...]]:
    conninfo = database_url.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(conninfo) as conn:
        return conn.execute(
            """
            SELECT s.token_hash, u.employee_no, s.created_at, s.last_seen_at
            FROM sessions s JOIN users u ON u.id = s.user_id
            ORDER BY s.created_at
            """
        ).fetchall()


def test_session_table_holds_the_hmac_of_the_token_not_the_token(seeded_database: SeededDatabase) -> None:
    settings = make_settings(seeded_database.url)
    app = make_app(settings)

    with api_client(app) as client:
        response = client.post(
            "/api/auth/login", json={"employee_no": "000003", "password": seeded_database.passwords["000003"]}
        )
        assert response.status_code == 200, response.text
        token = client.cookies.get("session")

    assert token
    key = settings.session_secret.get_secret_value().encode("utf-8")
    expected_hash = hmac.new(key, token.encode("utf-8"), hashlib.sha256).hexdigest()
    rows = _sessions(seeded_database.url)
    assert [(row[0], row[1]) for row in rows] == [(expected_hash, "000003")]
    assert all(token not in str(value) for row in rows for value in row)


def test_two_logins_get_different_tokens(seeded_database: SeededDatabase) -> None:
    app = make_app(make_settings(seeded_database.url))
    body = {"employee_no": "000001", "password": seeded_database.passwords["000001"]}

    with api_client(app) as first, api_client(app) as second:
        assert first.post("/api/auth/login", json=body).status_code == 200
        assert second.post("/api/auth/login", json=body).status_code == 200
        tokens = {first.cookies.get("session"), second.cookies.get("session")}

    assert None not in tokens
    assert len(tokens) == 2


@pytest.mark.parametrize("cookie_secure", [True, False])
def test_session_cookie_attributes(seeded_database: SeededDatabase, cookie_secure: bool) -> None:
    app = make_app(make_settings(seeded_database.url, cookie_secure=cookie_secure))

    with api_client(app) as client:
        response = client.post(
            "/api/auth/login", json={"employee_no": "000001", "password": seeded_database.passwords["000001"]}
        )

    assert response.status_code == 200, response.text
    set_cookies = response.headers.get_list("set-cookie")
    assert len(set_cookies) == 1
    attributes = [part.strip().lower() for part in set_cookies[0].split(";")]
    assert attributes[0].startswith("session=")
    assert "httponly" in attributes
    assert "samesite=lax" in attributes
    assert "path=/" in attributes
    assert ("secure" in attributes) is cookie_secure


def test_session_times_come_from_the_app_clock(seeded_database: SeededDatabase) -> None:
    start = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)
    clock = ManualClock(start)
    app = make_app(make_settings(seeded_database.url), clock=clock)

    with api_client(app) as client:
        login = client.post(
            "/api/auth/login", json={"employee_no": "000001", "password": seeded_database.passwords["000001"]}
        )
        assert login.status_code == 200, login.text
        assert [(row[2], row[3]) for row in _sessions(seeded_database.url)] == [(start, start)]

        clock.advance(timedelta(minutes=10))
        assert client.get("/api/me").status_code == 200

    assert [(row[2], row[3]) for row in _sessions(seeded_database.url)] == [(start, start + timedelta(minutes=10))]


@pytest.mark.parametrize("path", ["/api/auth/login", "/api/auth/logout"])
@pytest.mark.parametrize(
    "content_type", ["text/plain", "application/x-www-form-urlencoded", "multipart/form-data; boundary=x"]
)
def test_login_and_logout_accept_only_json(seeded_database: SeededDatabase, path: str, content_type: str) -> None:
    app = make_app(make_settings(seeded_database.url))
    body = f'{{"employee_no": "000001", "password": "{seeded_database.passwords["000001"]}"}}'

    with api_client(app) as client:
        response = client.post(path, content=body, headers={"Content-Type": content_type})
        cookies_after = dict(client.cookies)

    assert response.status_code == 415
    assert isinstance(response.json()["detail"], str)
    assert "session" not in cookies_after
    assert _sessions(seeded_database.url) == []


def test_logout_without_content_type_is_refused(seeded_database: SeededDatabase) -> None:
    app = make_app(make_settings(seeded_database.url))

    with api_client(app) as client:
        response = client.post("/api/auth/logout")

    assert response.status_code == 415


def test_json_with_charset_is_accepted(seeded_database: SeededDatabase) -> None:
    app = make_app(make_settings(seeded_database.url))
    body = f'{{"employee_no": "000001", "password": "{seeded_database.passwords["000001"]}"}}'

    with api_client(app) as client:
        response = client.post(
            "/api/auth/login", content=body, headers={"Content-Type": "application/json; charset=utf-8"}
        )

    assert response.status_code == 200, response.text


def test_login_logs_result_and_employee_no_but_not_secrets(
    seeded_database: SeededDatabase, caplog: pytest.LogCaptureFixture
) -> None:
    app = make_app(make_settings(seeded_database.url))
    password = seeded_database.passwords["000002"]
    wrong_password = secrets.token_urlsafe(16)

    with caplog.at_level(logging.INFO, logger="app"), api_client(app) as client:
        success = client.post("/api/auth/login", json={"employee_no": "000002", "password": password})
        assert success.status_code == 200, success.text
        token = client.cookies.get("session")
        failure = client.post("/api/auth/login", json={"employee_no": "000004", "password": wrong_password})
        assert failure.status_code == 401
        assert client.post("/api/auth/logout", json={}).status_code == 204

    assert token
    app_records = [record for record in caplog.records if record.name.startswith("app")]
    messages = [record.getMessage() for record in app_records]
    assert any("000002" in message for message in messages), messages
    assert any("000004" in message for message in messages), messages
    for secret in (password, wrong_password, token):
        assert secret not in caplog.text
