"""#38/TC-02: 誤ったパスワードと登録のない社員番号は 401 で、文が同じである(FR-002)。"""

import secrets

from tests.api_client import api_client
from tests.apps import make_app, make_settings
from tests.seeding import SeededDatabase

# 方式設計の「認証と認可の方式」の失敗の扱いの文
LOGIN_FAILED_MESSAGE = "社員番号かパスワードが違います"


def test_i38_tc02_wrong_password_and_unknown_employee_no_give_the_same_401(seeded_database: SeededDatabase) -> None:
    app = make_app(make_settings(seeded_database.url))
    wrong_password = secrets.token_urlsafe(16)
    assert wrong_password not in seeded_database.passwords.values()

    with api_client(app) as client:
        wrong = client.post("/api/auth/login", json={"employee_no": "000001", "password": wrong_password})
        unknown = client.post(
            "/api/auth/login", json={"employee_no": "999999", "password": seeded_database.passwords["000001"]}
        )
        cookies_after = dict(client.cookies)
        me = client.get("/api/me")

    assert wrong.status_code == 401
    assert unknown.status_code == 401
    assert wrong.json() == unknown.json() == {"detail": LOGIN_FAILED_MESSAGE}
    assert "session" not in cookies_after, "失敗したのにログインの状態の印が返っている"
    assert me.status_code == 401


def test_i38_tc02_another_users_password_does_not_log_in(seeded_database: SeededDatabase) -> None:
    app = make_app(make_settings(seeded_database.url))

    with api_client(app) as client:
        response = client.post(
            "/api/auth/login", json={"employee_no": "000001", "password": seeded_database.passwords["000004"]}
        )

    assert response.status_code == 401
    assert response.json() == {"detail": LOGIN_FAILED_MESSAGE}
