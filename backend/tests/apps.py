"""テストで API のアプリを組み立てる役。

鍵はそのたびに作る乱数にする。テストのクライアントは http で呼ぶので、既定ではクッキーに Secure を付けない
(Secure のクッキーは http では送り返されないため)。
"""

import secrets

from fastapi import FastAPI

from app.clock import Clock
from app.main import create_app
from app.settings import AppSettings, load_settings


def make_settings(database_url: str, *, cookie_secure: bool = False) -> AppSettings:
    """テストの設定。鍵はそのたびに作る乱数。"""
    return load_settings(
        {
            "DATABASE_URL": database_url,
            "SESSION_SECRET": secrets.token_urlsafe(32),
            "COOKIE_SECURE": "true" if cookie_secure else "false",
        }
    )


def make_app(settings: AppSettings, clock: Clock | None = None) -> FastAPI:
    """設定と時計を渡してアプリを組み立てる。"""
    return create_app(settings, clock=clock)
