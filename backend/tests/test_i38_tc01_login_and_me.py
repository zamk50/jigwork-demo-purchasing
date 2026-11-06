"""#38/TC-01: 移行と初期データのコマンドだけで入れた DB で、4 役割の利用者が API でログインできる。
ログイン中の利用者の API が社員番号・氏名・部署・役割を返し、000002 には社員と上長の 2 つの役割が返る
(FR-001・FR-009・FR-014・NFR-003)。
"""

from typing import Any

import pytest

from tests.api_client import api_client
from tests.apps import make_app, make_settings
from tests.seeding import SeededDatabase

# 方式設計の「初期データ」の節の表。役割は役割の並び順(社員・上長・購買担当・管理者)で返る
EXPECTED_ME: dict[str, dict[str, Any]] = {
    "000001": {
        "employee_no": "000001",
        "name": "社員 一郎",
        "department": "営業部",
        "roles": [{"code": "employee", "name": "社員"}],
    },
    "000002": {
        "employee_no": "000002",
        "name": "上長 二郎",
        "department": "営業部",
        "roles": [{"code": "employee", "name": "社員"}, {"code": "manager", "name": "上長"}],
    },
    "000003": {
        "employee_no": "000003",
        "name": "購買 三子",
        "department": "総務部",
        "roles": [{"code": "buyer", "name": "購買担当"}],
    },
    "000004": {
        "employee_no": "000004",
        "name": "管理 四郎",
        "department": "総務部",
        "roles": [{"code": "admin", "name": "管理者"}],
    },
}


@pytest.mark.parametrize("employee_no", list(EXPECTED_ME))
def test_i38_tc01_seeded_user_logs_in_and_me_returns_the_user(
    seeded_database: SeededDatabase, employee_no: str
) -> None:
    app = make_app(make_settings(seeded_database.url))
    password = seeded_database.passwords[employee_no]

    with api_client(app) as client:
        login = client.post("/api/auth/login", json={"employee_no": employee_no, "password": password})
        assert login.status_code == 200, login.text
        assert login.json() == EXPECTED_ME[employee_no]
        assert client.cookies.get("session"), "ログインの状態の印がクッキーで返っていない"

        me = client.get("/api/me")

    assert me.status_code == 200, me.text
    assert me.json() == EXPECTED_ME[employee_no]


def test_i38_tc01_manager_has_employee_and_manager_roles(seeded_database: SeededDatabase) -> None:
    app = make_app(make_settings(seeded_database.url))

    with api_client(app) as client:
        login = client.post(
            "/api/auth/login", json={"employee_no": "000002", "password": seeded_database.passwords["000002"]}
        )
        assert login.status_code == 200, login.text
        me = client.get("/api/me")

    assert me.status_code == 200, me.text
    assert [role["code"] for role in me.json()["roles"]] == ["employee", "manager"]
