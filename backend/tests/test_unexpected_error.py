"""想定しない例外の扱い(方式設計の「横断の方式」の「例外とログ」。Q-21 の答えで T-4 に入れた)。

想定しない例外は 500 と共通の文で返し、中身はログにだけ残す。想定した誤りの応答(404 など)は変えない。
"""

import logging
import secrets

import pytest

from tests.api_client import api_client
from tests.apps import make_app, make_settings
from tests.postgres import PostgresServer

# 画面共通規則の「メッセージの出し方」の、想定しない誤りの文
UNEXPECTED_ERROR_MESSAGE = "時間をおいてもう一度試してください"


def test_unexpected_exception_is_500_with_the_common_message_and_logged(
    postgres_server: PostgresServer, caplog: pytest.LogCaptureFixture
) -> None:
    app = make_app(make_settings(postgres_server.url()))
    detail = f"内部の詳しい事情 {secrets.token_hex(8)}"

    def failing_route() -> dict[str, str]:
        raise RuntimeError(detail)

    app.add_api_route("/test/fail", failing_route, methods=["GET"])

    with caplog.at_level(logging.ERROR, logger="app"), api_client(app, raise_server_exceptions=False) as client:
        response = client.get("/test/fail")

    assert response.status_code == 500
    assert response.json() == {"detail": UNEXPECTED_ERROR_MESSAGE}
    assert detail not in response.text
    errors = [record for record in caplog.records if record.name.startswith("app") and record.levelno >= logging.ERROR]
    assert errors, "想定しない例外がアプリのログに残っていない"
    assert detail in caplog.text


def test_expected_error_responses_are_unchanged(postgres_server: PostgresServer) -> None:
    app = make_app(make_settings(postgres_server.url()))

    with api_client(app, raise_server_exceptions=False) as client:
        response = client.get(f"/test/{secrets.token_hex(4)}")

    assert response.status_code == 404
