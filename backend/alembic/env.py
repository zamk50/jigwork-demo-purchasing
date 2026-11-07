"""Alembic の移行を流す入口。

接続先は、設定の sqlalchemy.url があればそれを使う(テストが渡す)。
無ければ環境変数 DATABASE_URL(または backend/.env)から読む。
"""

from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context
from app.db.models import Base
from app.settings import load_database_url

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name, disable_existing_loggers=False)

target_metadata = Base.metadata


def _database_url() -> str:
    return config.get_main_option("sqlalchemy.url") or load_database_url()


def run_migrations_offline() -> None:
    context.configure(url=_database_url(), target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    # 移行の例外の文にも、SQL に渡した値を載せない(方式設計の「例外とログ」)
    engine = create_engine(_database_url(), poolclass=pool.NullPool, hide_parameters=True)
    try:
        with engine.connect() as connection:
            context.configure(connection=connection, target_metadata=target_metadata)
            with context.begin_transaction():
                context.run_migrations()
    finally:
        engine.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
