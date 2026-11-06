"""口が使う共通の依存。骨組み。"""

from collections.abc import Iterator
from dataclasses import dataclass
from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session, sessionmaker

from app.clock import Clock
from app.settings import AppSettings


@dataclass(frozen=True)
class AppContext:
    """アプリが起動の時に組み立てて持つもの。"""

    settings: AppSettings
    clock: Clock
    session_factory: sessionmaker[Session]


def get_settings() -> AppSettings:
    raise NotImplementedError


def get_clock() -> Clock:
    raise NotImplementedError


def get_db() -> Iterator[Session]:
    raise NotImplementedError


CurrentSettings = Annotated[AppSettings, Depends(get_settings)]
CurrentClock = Annotated[Clock, Depends(get_clock)]
DbSession = Annotated[Session, Depends(get_db, scope="function")]
