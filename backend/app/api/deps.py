"""口が使う共通の依存(方式設計の「横断の方式」の節)。

- 設定・時計・パスワードの照合の役とダミーのハッシュは、アプリが起動の時に組み立てた AppContext から引く。
- DB のセッションは、要求 1 つを 1 つのトランザクションにする。
  - 口の関数が応答を返せば確定し、想定しない例外なら取り消す。
  - 401 などの想定した誤りは、例外にせず応答として返す。このため、誤りの応答の前の書き込みも確定する。
  - 確定は応答を送る前に行う(scope="function")。確定に失敗すれば 500 になり、確定していない応答を返さない。
"""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Annotated

from argon2 import PasswordHasher
from fastapi import Depends, Request
from sqlalchemy.orm import Session, sessionmaker

from app.clock import Clock
from app.settings import AppSettings


@dataclass(frozen=True)
class AppContext:
    """アプリが起動の時に組み立てて持つもの。"""

    settings: AppSettings
    clock: Clock
    session_factory: sessionmaker[Session]
    password_hasher: PasswordHasher
    dummy_password_hash: str
    """照合の要らないログインの失敗で照らすダミーのハッシュ(決定 D-09)。password_hasher と同じ強さで作る。"""


def get_context(request: Request) -> AppContext:
    """アプリの AppContext を返す。"""
    context: AppContext = request.app.state.context
    return context


AppContextDep = Annotated[AppContext, Depends(get_context)]


def get_settings(context: AppContextDep) -> AppSettings:
    """アプリの設定を返す。"""
    return context.settings


def get_clock(context: AppContextDep) -> Clock:
    """アプリの時計を返す。"""
    return context.clock


def get_password_hasher(context: AppContextDep) -> PasswordHasher:
    """パスワードの照合の役(argon2id)を返す。"""
    return context.password_hasher


def get_dummy_password_hash(context: AppContextDep) -> str:
    """照合の要らないログインの失敗で照らすダミーのハッシュを返す。"""
    return context.dummy_password_hash


def get_db(context: AppContextDep) -> Iterator[Session]:
    """要求 1 つ分のトランザクションを張ったセッションを返す。"""
    with context.session_factory() as session, session.begin():
        yield session


CurrentSettings = Annotated[AppSettings, Depends(get_settings)]
CurrentClock = Annotated[Clock, Depends(get_clock)]
CurrentPasswordHasher = Annotated[PasswordHasher, Depends(get_password_hasher)]
DummyPasswordHash = Annotated[str, Depends(get_dummy_password_hash)]
DbSession = Annotated[Session, Depends(get_db, scope="function")]
