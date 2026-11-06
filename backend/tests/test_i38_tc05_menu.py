"""#38/TC-05: メニューの API が、役割ごとの項目表の項目だけを返す。000002 には社員の 3 項目の後に
上長の 1 項目が並ぶ。準備中の項目は使えない印を持つ(FR-015〜FR-019)。

応答の形(方式設計の「API」「メニューの項目の持ち方」):

    {"groups": [{"role": {"code": ..., "name": ...},
                 "items": [{"code": ..., "name": ..., "available": ...}, ...]}, ...]}

期待値は、要件の項目表(FR-016)をここに書き写したものである。役割は役割の順(FR-017)に並ぶ。
"""

from typing import Any

import httpx
import pytest

from tests.api_client import api_client
from tests.apps import make_app, make_settings
from tests.seeding import SeededDatabase

# 要件の項目表(FR-016)。役割の順(社員・上長・購買担当・管理者)
EMPLOYEE_ITEMS = ["品目の検索", "購入依頼の入力", "自分の依頼の一覧"]
MANAGER_ITEMS = ["決裁待ちの一覧(自部署)"]
BUYER_ITEMS = ["発注", "入荷の登録", "在庫の一覧", "品目の管理", "月次の集計", "会計への書き出し"]
ADMIN_ITEMS = ["仕入先の管理", "区分の管理", "利用者と役割の管理"]

# 初期データの利用者ごとの、役割(コード・名前)と項目の名前の並び
EXPECTED_MENU: dict[str, list[tuple[str, str, list[str]]]] = {
    "000001": [("employee", "社員", EMPLOYEE_ITEMS)],
    "000002": [("employee", "社員", EMPLOYEE_ITEMS), ("manager", "上長", MANAGER_ITEMS)],
    "000003": [("buyer", "購買担当", BUYER_ITEMS)],
    "000004": [("admin", "管理者", ADMIN_ITEMS)],
}


def _menu_of(client: httpx.Client, seeded_database: SeededDatabase, employee_no: str) -> dict[str, Any]:
    login = client.post(
        "/api/auth/login", json={"employee_no": employee_no, "password": seeded_database.passwords[employee_no]}
    )
    assert login.status_code == 200, login.text
    menu = client.get("/api/menu")
    assert menu.status_code == 200, menu.text
    body: dict[str, Any] = menu.json()
    return body


def _shape(body: dict[str, Any]) -> list[tuple[str, str, list[str]]]:
    return [
        (group["role"]["code"], group["role"]["name"], [item["name"] for item in group["items"]])
        for group in body["groups"]
    ]


@pytest.mark.parametrize("employee_no", list(EXPECTED_MENU))
def test_i38_tc05_menu_returns_only_the_items_of_the_users_roles(
    seeded_database: SeededDatabase, employee_no: str
) -> None:
    app = make_app(make_settings(seeded_database.url))

    with api_client(app) as client:
        body = _menu_of(client, seeded_database, employee_no)

    assert _shape(body) == EXPECTED_MENU[employee_no]


def test_i38_tc05_manager_gets_employee_items_then_manager_item(seeded_database: SeededDatabase) -> None:
    app = make_app(make_settings(seeded_database.url))

    with api_client(app) as client:
        body = _menu_of(client, seeded_database, "000002")

    names = [item["name"] for group in body["groups"] for item in group["items"]]
    assert names == [*EMPLOYEE_ITEMS, *MANAGER_ITEMS]
    for other in [*BUYER_ITEMS, *ADMIN_ITEMS]:
        assert other not in names, f"ほかの役割の項目が返っている: {other}"


def test_i38_tc05_items_without_a_screen_are_not_available(seeded_database: SeededDatabase) -> None:
    """この Issue では、どの項目も先の画面がないので、すべて使えない(準備中)の印を持つ。"""
    app = make_app(make_settings(seeded_database.url))
    items: list[dict[str, Any]] = []

    with api_client(app) as client:
        for employee_no in EXPECTED_MENU:
            items.extend(
                item for group in _menu_of(client, seeded_database, employee_no)["groups"] for item in group["items"]
            )
            assert client.post("/api/auth/logout", json={}).status_code == 204

    assert len(items) == len(EMPLOYEE_ITEMS) * 2 + len(MANAGER_ITEMS) + len(BUYER_ITEMS) + len(ADMIN_ITEMS)
    assert all(item["available"] is False for item in items), items
    # 項目コードは空でない文字列で、同じ名前の項目は同じコードを持ち、名前の違う項目どうしで重ならない
    code_by_name: dict[str, str] = {}
    for item in items:
        assert isinstance(item["code"], str)
        assert item["code"]
        assert code_by_name.setdefault(item["name"], item["code"]) == item["code"]
    assert len(set(code_by_name.values())) == len(code_by_name)
