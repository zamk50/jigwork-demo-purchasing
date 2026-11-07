"""ログインの失敗のログに、数字 6 桁でない社員番号の値を出さない(方式設計の「横断の方式」の「例外とログ」)。

社員番号の欄にパスワードを入れて API を直に呼んでも、その文字列はログに残らない。
形の誤りは「形の誤り」とだけ書く。正しい形の社員番号は、これまでどおりログに書く。
"""

import logging
import secrets

import pytest

from tests.api_client import api_client
from tests.apps import make_app, make_settings
from tests.seeding import SeededDatabase

# 方式設計の「認証と認可の方式」の失敗の扱いの文
LOGIN_FAILED_MESSAGE = "社員番号かパスワードが違います"


def _app_messages(caplog: pytest.LogCaptureFixture) -> list[str]:
    return [record.getMessage() for record in caplog.records if record.name.startswith("app")]


@pytest.mark.parametrize(
    "employee_no",
    [
        f"Pw-{secrets.token_urlsafe(16)}!",
        f"{secrets.token_hex(3)}{secrets.token_urlsafe(8)}",
        "1234567890" * 20,
    ],
    ids=["password_like", "mixed_text", "long_digits"],
)
def test_malformed_employee_no_is_not_written_to_the_log(
    seeded_database: SeededDatabase, caplog: pytest.LogCaptureFixture, employee_no: str
) -> None:
    app = make_app(make_settings(seeded_database.url))

    with caplog.at_level(logging.INFO, logger="app"), api_client(app) as client:
        response = client.post("/api/auth/login", json={"employee_no": employee_no, "password": secrets.token_hex(8)})

    assert response.status_code == 401, response.text
    assert response.json() == {"detail": LOGIN_FAILED_MESSAGE}
    messages = _app_messages(caplog)
    assert any("ログインに失敗した" in message and "形の誤り" in message for message in messages), messages
    assert employee_no not in caplog.text


def test_a_real_password_typed_as_the_employee_no_is_not_logged(
    seeded_database: SeededDatabase, caplog: pytest.LogCaptureFixture
) -> None:
    app = make_app(make_settings(seeded_database.url))
    password = seeded_database.passwords["000001"]

    with caplog.at_level(logging.INFO, logger="app"), api_client(app) as client:
        response = client.post("/api/auth/login", json={"employee_no": password, "password": password})

    assert response.status_code == 401, response.text
    assert password not in caplog.text


def test_well_formed_employee_no_is_still_logged_on_failure(
    seeded_database: SeededDatabase, caplog: pytest.LogCaptureFixture
) -> None:
    app = make_app(make_settings(seeded_database.url))

    with caplog.at_level(logging.INFO, logger="app"), api_client(app) as client:
        response = client.post("/api/auth/login", json={"employee_no": "999999", "password": secrets.token_hex(8)})

    assert response.status_code == 401, response.text
    messages = _app_messages(caplog)
    assert any("ログインに失敗した" in message and "999999" in message for message in messages), messages
