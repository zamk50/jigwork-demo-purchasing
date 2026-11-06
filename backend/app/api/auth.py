"""口: ログイン・ログアウト・ログイン中の利用者(方式設計の「API」「認証と認可の方式」)。

- ログインの状態の印は、クッキー session で受け渡す。属性は HttpOnly・SameSite=Lax・Path=/ で、設定で Secure も付ける。
- ログイン・ログアウトは Content-Type が application/json の要求だけを受ける(要求の偽造への備え)。
- 401 などの想定した誤りは、例外にせず応答として返す(要求ごとのトランザクションで、その前の書き込みを確定するため)。
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from app.api.deps import CurrentClock, CurrentPasswordHasher, CurrentSettings, DbSession, DummyPasswordHash
from app.auth.service import (
    LOGIN_FAILED_MESSAGE,
    LoginUser,
    authenticate,
    delete_expired_sessions,
    end_session,
    hash_token,
    load_login_user,
    new_token,
    resume_session,
    start_session,
)
from app.settings import AppSettings

logger = logging.getLogger("app.auth")

SESSION_COOKIE = "session"
LOGIN_REQUIRED_MESSAGE = "ログインしてください"
JSON_REQUIRED_MESSAGE = "JSON(Content-Type: application/json)で送ってください"

router = APIRouter(prefix="/api")


class LoginRequest(BaseModel):
    """ログインの要求。社員番号の形(数字 6 桁)の誤りも、ほかの失敗と同じ 401 にする(FR-024)。"""

    employee_no: str
    password: str


class RoleResponse(BaseModel):
    """役割 1 つ。"""

    code: str
    name: str


class MeResponse(BaseModel):
    """ログイン中の利用者(FR-009・FR-014)。役割は役割の並び順。"""

    employee_no: str
    name: str
    department: str
    roles: list[RoleResponse]


class ErrorResponse(BaseModel):
    """誤りの応答。"""

    detail: str


def require_json(request: Request) -> None:
    """Content-Type が application/json でなければ 415 で断る。"""
    content_type = request.headers.get("content-type", "")
    media_type = content_type.split(";", 1)[0].strip().lower()
    if media_type != "application/json":
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=JSON_REQUIRED_MESSAGE)


SessionToken = Annotated[str | None, Cookie(alias=SESSION_COOKIE)]


def get_login_user(
    db: DbSession, clock: CurrentClock, settings: CurrentSettings, token: SessionToken = None
) -> LoginUser | None:
    """クッキーの印からログイン中の利用者を引く。ログインしていなければ None を返す。"""
    if not token:
        return None
    user = resume_session(db, hash_token(settings.session_secret.get_secret_value(), token), clock.now())
    if user is None:
        return None
    return load_login_user(db, user)


OptionalLoginUser = Annotated[LoginUser | None, Depends(get_login_user)]


def _error(status_code: int, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status_code, content=ErrorResponse(detail=detail).model_dump())


def _me(user: LoginUser) -> MeResponse:
    return MeResponse(
        employee_no=user.employee_no,
        name=user.name,
        department=user.department,
        roles=[RoleResponse(code=role.code, name=role.name) for role in user.roles],
    )


def _set_session_cookie(response: Response, settings: AppSettings, token: str) -> None:
    response.set_cookie(SESSION_COOKIE, token, path="/", httponly=True, samesite="lax", secure=settings.cookie_secure)


@router.post(
    "/auth/login",
    response_model=MeResponse,
    responses={401: {"model": ErrorResponse}, 415: {"model": ErrorResponse}},
    dependencies=[Depends(require_json)],
)
def login(
    body: LoginRequest,
    response: Response,
    db: DbSession,
    clock: CurrentClock,
    settings: CurrentSettings,
    hasher: CurrentPasswordHasher,
    dummy_password_hash: DummyPasswordHash,
) -> MeResponse | JSONResponse:
    """ログインする。成功ならログインの状態を作り、印をクッキーで返す。

    失敗(登録のない社員番号・数字 6 桁でない社員番号・誤ったパスワード・ロック中・役割なし)は、
    どれも 401 と共通の文で返す。誤った回数とロックの書き込みは、401 を返しても確定する。
    """
    now = clock.now()
    delete_expired_sessions(db, now)
    user = authenticate(db, hasher, dummy_password_hash, body.employee_no, body.password, now)
    if user is None:
        logger.info("ログインに失敗した 社員番号=%r", body.employee_no)
        return _error(status.HTTP_401_UNAUTHORIZED, LOGIN_FAILED_MESSAGE)

    token = new_token()
    start_session(db, user, hash_token(settings.session_secret.get_secret_value(), token), now)
    _set_session_cookie(response, settings, token)
    logger.info("ログインに成功した 社員番号=%r", body.employee_no)
    return _me(load_login_user(db, user))


@router.post(
    "/auth/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={415: {"model": ErrorResponse}},
    dependencies=[Depends(require_json)],
)
def logout(db: DbSession, settings: CurrentSettings, token: SessionToken = None) -> Response:
    """ログアウトする。その印のログインの状態を消し、クッキーを消す。ログインの状態がなくても 204。"""
    if token:
        end_session(db, hash_token(settings.session_secret.get_secret_value(), token))
    response = Response(status_code=status.HTTP_204_NO_CONTENT)
    response.delete_cookie(SESSION_COOKIE, path="/", httponly=True, samesite="lax", secure=settings.cookie_secure)
    return response


@router.get("/me", response_model=MeResponse, responses={401: {"model": ErrorResponse}})
def me(user: OptionalLoginUser) -> MeResponse | JSONResponse:
    """ログイン中の利用者を返す。ログインしていなければ 401。"""
    if user is None:
        return _error(status.HTTP_401_UNAUTHORIZED, LOGIN_REQUIRED_MESSAGE)
    return _me(user)
