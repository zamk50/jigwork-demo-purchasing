"""#38/TC-06: ログインせずにメニューの API を呼ぶと 401 である(FR-008)。

ログイン中の利用者の API の分は test_i38_tc06_requires_login.py で確かめる。
"""

import secrets

from tests.api_client import api_client
from tests.apps import make_app, make_settings
from tests.seeding import SeededDatabase


def test_i38_tc06_menu_without_login_is_401(seeded_database: SeededDatabase) -> None:
    app = make_app(make_settings(seeded_database.url))

    with api_client(app) as client:
        response = client.get("/api/menu")

    assert response.status_code == 401
    assert isinstance(response.json()["detail"], str)


def test_i38_tc06_menu_with_an_unknown_session_cookie_is_401(seeded_database: SeededDatabase) -> None:
    app = make_app(make_settings(seeded_database.url))

    with api_client(app) as client:
        response = client.get("/api/menu", headers={"Cookie": f"session={secrets.token_urlsafe(32)}"})

    assert response.status_code == 401
