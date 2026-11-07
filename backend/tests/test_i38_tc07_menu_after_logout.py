"""#38/TC-07: ログアウトの後、前のクッキーでメニューの API を呼ぶと 401 である(FR-013-AC-02)。

ログイン中の利用者の API の分と、ログインの状態がないときのログアウトは test_i38_tc07_logout.py で確かめる。
"""

from tests.api_client import api_client
from tests.apps import make_app, make_settings
from tests.seeding import SeededDatabase


def test_i38_tc07_menu_with_the_old_cookie_is_401_after_logout(seeded_database: SeededDatabase) -> None:
    app = make_app(make_settings(seeded_database.url))

    with api_client(app) as client:
        login = client.post(
            "/api/auth/login", json={"employee_no": "000001", "password": seeded_database.passwords["000001"]}
        )
        assert login.status_code == 200, login.text
        token = client.cookies.get("session")
        assert token
        assert client.get("/api/menu").status_code == 200

        logout = client.post("/api/auth/logout", json={})
        assert logout.status_code == 204
        assert client.get("/api/menu").status_code == 401

    with api_client(app) as other:
        old = other.get("/api/menu", headers={"Cookie": f"session={token}"})
    assert old.status_code == 401
