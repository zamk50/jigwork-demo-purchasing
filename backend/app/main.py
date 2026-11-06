"""API のサーバーの入口。骨組み。"""

from fastapi import FastAPI

from app.clock import Clock
from app.settings import AppSettings


def create_app(settings: AppSettings | None = None, clock: Clock | None = None) -> FastAPI:
    """アプリを組み立てる。"""
    raise NotImplementedError
