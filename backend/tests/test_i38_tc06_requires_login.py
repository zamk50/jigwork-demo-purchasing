"""#38/TC-06: ログインせずにログイン中の利用者の API を呼ぶと 401 である(FR-008)。

メニューの API はタスク T-6 で作るので、そのタスクでここに足す。
"""

import secrets

from tests.api_client import api_client
from tests.apps import make_app, make_settings
from tests.seeding import SeededDatabase


def test_i38_tc06_me_without_login_is_401(seeded_database: SeededDatabase) -> None:
    app = make_app(make_settings(seeded_database.url))

    with api_client(app) as client:
        response = client.get("/api/me")

    assert response.status_code == 401
    assert isinstance(response.json()["detail"], str)


def test_i38_tc06_me_with_an_unknown_session_cookie_is_401(seeded_database: SeededDatabase) -> None:
    app = make_app(make_settings(seeded_database.url))

    with api_client(app) as client:
        response = client.get("/api/me", headers={"Cookie": f"session={secrets.token_urlsafe(32)}"})

    assert response.status_code == 401
