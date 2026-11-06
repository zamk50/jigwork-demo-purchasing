"""口: メニュー(方式設計の「API」「メニューの項目の持ち方」。FR-015〜FR-019)。

ログインの要る口で、ログインしていなければ 401 を返す(FR-008)。
返すのは、ログイン中の利用者の役割の項目だけである(FR-018)。
"""

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.auth import LOGIN_REQUIRED_MESSAGE, ErrorResponse, OptionalLoginUser, RoleResponse
from app.menu.service import MenuGroup, build_menu

router = APIRouter(prefix="/api")


class MenuItemResponse(BaseModel):
    """メニューの項目 1 つ。available が偽なら、先の画面がまだない(準備中。FR-019)。"""

    code: str
    name: str
    available: bool


class MenuGroupResponse(BaseModel):
    """役割 1 つ分の項目のまとまり。"""

    role: RoleResponse
    items: list[MenuItemResponse]


class MenuResponse(BaseModel):
    """メニュー。役割の順(社員・上長・購買担当・管理者。FR-017)に、役割ごとにまとめて並べる。"""

    groups: list[MenuGroupResponse]


def _group(group: MenuGroup) -> MenuGroupResponse:
    return MenuGroupResponse(
        role=RoleResponse(code=group.role.code, name=group.role.name),
        items=[MenuItemResponse(code=item.code, name=item.name, available=item.available) for item in group.items],
    )


@router.get("/menu", response_model=MenuResponse, responses={401: {"model": ErrorResponse}})
def menu(user: OptionalLoginUser) -> MenuResponse | JSONResponse:
    """ログイン中の利用者のメニューを返す。ログインしていなければ 401。"""
    if user is None:
        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content=ErrorResponse(detail=LOGIN_REQUIRED_MESSAGE).model_dump(),
        )
    return MenuResponse(groups=[_group(group) for group in build_menu(user.roles)])
