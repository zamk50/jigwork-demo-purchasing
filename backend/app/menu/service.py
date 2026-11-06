"""役割に応じたメニューを組み立てる業務の処理(FR-015〜FR-019。決定 D-03)。

業務の層なので FastAPI の型に頼らない。

- 項目表(FR-016)は、このモジュールの定数に持つ。DB の表にはしない(決定 D-03)。
- 項目は、項目コード・名前・役割・並び順・使えるかを持つ。並び順は、項目表の役割の行の中の順である。
- メニューは、項目表の役割の順(社員・上長・購買担当・管理者。FR-017)に、利用者の持つ役割の行だけを並べる。
  ほかの役割の項目は組み立てない(FR-018)。
- 先の画面がまだない項目は、使えない(準備中)とする(FR-019)。この Issue では、すべての項目が使えない。
  業務の画面を足す Issue で、その項目を使えるにして行き先を足す。
- 項目は役割の行どうしで重ならない(FNC-003 の「例外と境界」)。
"""

from collections.abc import Iterable
from dataclasses import dataclass

from app.auth.service import RoleInfo


@dataclass(frozen=True)
class MenuItem:
    """メニューの項目 1 つ。"""

    code: str
    name: str
    role_code: str
    sort_order: int
    available: bool


@dataclass(frozen=True)
class MenuGroup:
    """役割 1 つ分の項目のまとまり。"""

    role: RoleInfo
    items: tuple[MenuItem, ...]


def _row(role_code: str, items: Iterable[tuple[str, str]]) -> tuple[str, tuple[MenuItem, ...]]:
    """項目表の役割の行を作る。項目は (項目コード, 名前) の並びで、並び順はこの並びの順とする。"""
    return (
        role_code,
        tuple(
            MenuItem(code=code, name=name, role_code=role_code, sort_order=index, available=False)
            for index, (code, name) in enumerate(items, start=1)
        ),
    )


# 項目表(FR-016)。役割の順(FR-017)に並べる。お知らせと発注書の項目は、それぞれの機能の Issue で足す
MENU_TABLE: tuple[tuple[str, tuple[MenuItem, ...]], ...] = (
    _row(
        "employee",
        [
            ("item_search", "品目の検索"),
            ("purchase_request_entry", "購入依頼の入力"),
            ("my_requests", "自分の依頼の一覧"),
        ],
    ),
    _row(
        "manager",
        [
            ("approval_queue", "決裁待ちの一覧(自部署)"),
        ],
    ),
    _row(
        "buyer",
        [
            ("purchase_order", "発注"),
            ("receiving_entry", "入荷の登録"),
            ("stock_list", "在庫の一覧"),
            ("item_master", "品目の管理"),
            ("monthly_summary", "月次の集計"),
            ("accounting_export", "会計への書き出し"),
        ],
    ),
    _row(
        "admin",
        [
            ("supplier_master", "仕入先の管理"),
            ("category_master", "区分の管理"),
            ("user_role_admin", "利用者と役割の管理"),
        ],
    ),
)


def build_menu(roles: Iterable[RoleInfo]) -> tuple[MenuGroup, ...]:
    """利用者の持つ役割の項目だけを、項目表の役割の順に組み立てる。項目表にない役割は出さない。"""
    by_code = {role.code: role for role in roles}
    return tuple(
        MenuGroup(role=by_code[role_code], items=items) for role_code, items in MENU_TABLE if role_code in by_code
    )
