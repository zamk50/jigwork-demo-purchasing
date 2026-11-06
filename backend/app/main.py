"""API のサーバーの入口。

起動(backend/ で):

    uvicorn app.main:create_app --factory

起動の時に設定を読み、DB の接続先(DATABASE_URL)かログインの状態の鍵(SESSION_SECRET)が
無いか正しくなければ、SettingsError で止まる(NFR-007)。
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api.deps import AppContext
from app.clock import Clock, SystemClock
from app.settings import AppSettings, load_settings


def create_app(settings: AppSettings | None = None, clock: Clock | None = None) -> FastAPI:
    """アプリを組み立てる。

    settings を渡さなければ、環境変数(と .env)から読む。clock を渡さなければ本物の時計を使う。
    DB にはここでは繋がない(接続は最初の要求の時に張る)。
    """
    if settings is None:
        settings = load_settings()
    engine = create_engine(settings.database_url, pool_pre_ping=True)
    context = AppContext(
        settings=settings,
        clock=clock if clock is not None else SystemClock(),
        session_factory=sessionmaker(engine, expire_on_commit=False),
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(title="購買と在庫の業務アプリ", lifespan=lifespan)
    app.state.context = context
    return app
