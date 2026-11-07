"""API のサーバーの入口。

起動(backend/ で):

    uvicorn app.main:create_app --factory

起動の時に設定を読み、DB の接続先(DATABASE_URL)かログインの状態の鍵(SESSION_SECRET)が
無いか正しくなければ、SettingsError で止まる(NFR-007)。
"""

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from argon2 import PasswordHasher
from fastapi import FastAPI
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.api import auth, menu
from app.api.deps import AppContext
from app.api.errors import install_error_handlers
from app.auth.service import make_dummy_password_hash
from app.clock import Clock, SystemClock
from app.log import configure_logging
from app.settings import AppSettings, load_settings


def create_app(
    settings: AppSettings | None = None,
    clock: Clock | None = None,
    password_hasher: PasswordHasher | None = None,
) -> FastAPI:
    """アプリを組み立てる。

    settings を渡さなければ、環境変数(と .env)から読む。clock を渡さなければ本物の時計を使う。
    password_hasher を渡さなければ、argon2-cffi の既定の強さの argon2id を使う(決定 D-02)。
    照合の要らないログインの失敗で照らすダミーのハッシュは、ここで照合の役と同じ強さで作る(決定 D-09)。
    DB にはここでは繋がない(接続は最初の要求の時に張る)。
    """
    if settings is None:
        settings = load_settings()
    configure_logging()
    # 想定しない例外のログに、SQL に渡した値(社員番号など)を載せない
    engine = create_engine(settings.database_url, pool_pre_ping=True, hide_parameters=True)
    hasher = password_hasher if password_hasher is not None else PasswordHasher()
    context = AppContext(
        settings=settings,
        clock=clock if clock is not None else SystemClock(),
        session_factory=sessionmaker(engine, expire_on_commit=False),
        password_hasher=hasher,
        dummy_password_hash=make_dummy_password_hash(hasher),
    )

    @asynccontextmanager
    async def lifespan(_app: FastAPI) -> AsyncGenerator[None]:
        try:
            yield
        finally:
            engine.dispose()

    app = FastAPI(title="購買と在庫の業務アプリ", lifespan=lifespan)
    app.state.context = context
    install_error_handlers(app)
    app.include_router(auth.router)
    app.include_router(menu.router)
    return app
