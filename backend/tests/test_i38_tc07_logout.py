"""#38/TC-07: ログアウトの後、前のクッキーでログインの要る API を呼ぶと 401 である。
ログインの状態がなくてもログアウトは 204 である(FR-012・FR-013)。

メニューの API はタスク T-6 で作るので、それまではログイン中の利用者の API で確かめる。
"""

import secrets

import psycopg

from tests.api_client import api_client
from tests.apps import make_app, make_settings
from tests.seeding import SeededDatabase


def _session_count(database_url: str) -> int:
    conninfo = database_url.replace("postgresql+psycopg://", "postgresql://")
    with psycopg.connect(conninfo) as conn:
        row = conn.execute("SELECT count(*) FROM sessions").fetchone()
    assert row is not None
    return int(row[0])


def test_i38_tc07_old_cookie_is_401_after_logout(seeded_database: SeededDatabase) -> None:
    app = make_app(make_settings(seeded_database.url))

    with api_client(app) as client:
        login = client.post(
            "/api/auth/login", json={"employee_no": "000001", "password": seeded_database.passwords["000001"]}
        )
        assert login.status_code == 200, login.text
        token = client.cookies.get("session")
        assert token
        assert client.get("/api/me").status_code == 200
        assert _session_count(seeded_database.url) == 1

        logout = client.post("/api/auth/logout", json={})
        assert logout.status_code == 204
        assert client.cookies.get("session") is None, "ログアウトでクッキーが消えていない"
        assert client.get("/api/me").status_code == 401

    assert _session_count(seeded_database.url) == 0

    with api_client(app) as other:
        old = other.get("/api/me", headers={"Cookie": f"session={token}"})
    assert old.status_code == 401


def test_i38_tc07_logout_without_a_session_is_204(seeded_database: SeededDatabase) -> None:
    app = make_app(make_settings(seeded_database.url))

    with api_client(app) as client:
        no_cookie = client.post("/api/auth/logout", json={})
        unknown = client.post("/api/auth/logout", json={}, headers={"Cookie": f"session={secrets.token_urlsafe(32)}"})

    assert no_cookie.status_code == 204
    assert unknown.status_code == 204
