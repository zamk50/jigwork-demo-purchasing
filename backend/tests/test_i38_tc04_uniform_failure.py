"""#38/TC-04: 6 桁でない社員番号と役割なしの利用者は 401 で、文が同じである。
どの失敗でも照合を 1 回呼ぶ(FR-023・FR-024・決定 D-09)。

照合の回数は、照合の役(argon2id の PasswordHasher)を、呼ばれた回数を数えるものに差し替えて確かめる。
"""

import secrets
from datetime import UTC, datetime, timedelta
from typing import Literal, override

import httpx
import psycopg
import pytest
from argon2 import PasswordHasher

from app.main import create_app
from tests.api_client import api_client
from tests.apps import make_settings
from tests.clock import ManualClock
from tests.seeding import SeededDatabase

# 方式設計の「認証と認可の方式」の失敗の扱いの文
LOGIN_FAILED_MESSAGE = "社員番号かパスワードが違います"

START = datetime(2026, 4, 1, 9, 0, tzinfo=UTC)

MALFORMED_EMPLOYEE_NOS = [
    "",
    "00001",
    "0000001",
    "00000a",
    "abcdef",
    " 000001",
    "000001 ",
    "000001\n",
    "00000" + chr(0xFF11),  # 末尾が全角の 1
    chr(0x0660) * 5 + chr(0x0661),  # アラビア文字の数字の 000001
    "1" * 1000,
]


class CountingPasswordHasher(PasswordHasher):
    """照合(verify)を呼んだ回数を数える argon2id の照合の役。"""

    def __init__(self) -> None:
        super().__init__()
        self.verify_calls = 0

    @override
    def verify(self, hash: str | bytes, password: str | bytes) -> Literal[True]:
        self.verify_calls += 1
        return super().verify(hash, password)


def _sessions_count(database_url: str) -> int:
    conninfo = database_url.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(conninfo) as conn:
        row = conn.execute("SELECT count(*) FROM sessions").fetchone()
    assert row is not None
    return int(row[0])


def _remove_roles(database_url: str, employee_no: str) -> None:
    conninfo = database_url.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(conninfo) as conn:
        conn.execute(
            "DELETE FROM user_roles WHERE user_id = (SELECT id FROM users WHERE employee_no = %s)", (employee_no,)
        )


def _failed_login_count(database_url: str, employee_no: str) -> int:
    conninfo = database_url.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(conninfo) as conn:
        row = conn.execute("SELECT failed_login_count FROM users WHERE employee_no = %s", (employee_no,)).fetchone()
    assert row is not None
    return int(row[0])


def _login(client: httpx.Client, employee_no: str, password: str) -> httpx.Response:
    return client.post("/api/auth/login", json={"employee_no": employee_no, "password": password})


def _assert_failed(response: httpx.Response) -> None:
    assert response.status_code == 401, response.text
    assert response.json() == {"detail": LOGIN_FAILED_MESSAGE}


@pytest.mark.parametrize("employee_no", MALFORMED_EMPLOYEE_NOS)
def test_i38_tc04_malformed_employee_no_is_the_same_401(seeded_database: SeededDatabase, employee_no: str) -> None:
    hasher = CountingPasswordHasher()
    app = create_app(make_settings(seeded_database.url), password_hasher=hasher)

    with api_client(app) as client:
        before = hasher.verify_calls
        response = _login(client, employee_no, seeded_database.passwords["000001"])
        calls = hasher.verify_calls - before
        cookies_after = dict(client.cookies)

    _assert_failed(response)
    assert calls == 1
    assert "session" not in cookies_after
    assert _sessions_count(seeded_database.url) == 0
    assert _failed_login_count(seeded_database.url, "000001") == 0


def test_i38_tc04_user_without_roles_cannot_log_in(seeded_database: SeededDatabase) -> None:
    _remove_roles(seeded_database.url, "000003")
    hasher = CountingPasswordHasher()
    app = create_app(make_settings(seeded_database.url), password_hasher=hasher)

    with api_client(app) as client:
        before = hasher.verify_calls
        response = _login(client, "000003", seeded_database.passwords["000003"])
        calls = hasher.verify_calls - before
        cookies_after = dict(client.cookies)
        me = client.get("/api/me")

    _assert_failed(response)
    assert calls == 1
    assert "session" not in cookies_after
    assert me.status_code == 401
    assert _sessions_count(seeded_database.url) == 0


def test_i38_tc04_every_failure_and_success_verifies_once(seeded_database: SeededDatabase) -> None:
    _remove_roles(seeded_database.url, "000003")
    hasher = CountingPasswordHasher()
    clock = ManualClock(START)
    app = create_app(make_settings(seeded_database.url), clock=clock, password_hasher=hasher)
    password = seeded_database.passwords["000001"]
    wrong = secrets.token_urlsafe(16)
    assert wrong not in seeded_database.passwords.values()

    attempts: list[tuple[str, int]] = []

    def attempt(client: httpx.Client, label: str, employee_no: str, given_password: str) -> httpx.Response:
        before = hasher.verify_calls
        response = _login(client, employee_no, given_password)
        attempts.append((label, hasher.verify_calls - before))
        return response

    with api_client(app) as client:
        _assert_failed(attempt(client, "登録のない社員番号", "999999", password))
        _assert_failed(attempt(client, "数字 6 桁でない社員番号", "12345", password))
        _assert_failed(attempt(client, "役割なし", "000003", seeded_database.passwords["000003"]))
        for _ in range(5):
            _assert_failed(attempt(client, "誤ったパスワード", "000001", wrong))
        _assert_failed(attempt(client, "ロック中の誤ったパスワード", "000001", wrong))
        _assert_failed(attempt(client, "ロック中の正しいパスワード", "000001", password))
        clock.advance(timedelta(minutes=15, seconds=1))
        success = attempt(client, "成功", "000001", password)

    assert success.status_code == 200, success.text
    assert attempts == [(label, 1) for label, _ in attempts]


def test_i38_tc04_failure_bodies_are_identical(seeded_database: SeededDatabase) -> None:
    _remove_roles(seeded_database.url, "000003")
    clock = ManualClock(START)
    app = create_app(make_settings(seeded_database.url), clock=clock)
    password = seeded_database.passwords["000001"]
    wrong = secrets.token_urlsafe(16)
    assert wrong not in seeded_database.passwords.values()

    with api_client(app) as client:
        responses = [
            _login(client, "999999", password),
            _login(client, "1234567", password),
            _login(client, "000003", seeded_database.passwords["000003"]),
        ]
        responses.extend(_login(client, "000001", wrong) for _ in range(5))
        responses.append(_login(client, "000001", password))

    assert {response.status_code for response in responses} == {401}
    assert {response.content for response in responses} == {responses[0].content}
    assert responses[0].json() == {"detail": LOGIN_FAILED_MESSAGE}
