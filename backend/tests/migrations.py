"""テストから Alembic の移行を流す役。"""

from pathlib import Path

from alembic import command
from alembic.config import Config

BACKEND = Path(__file__).resolve().parents[1]


def alembic_config(database_url: str) -> Config:
    """backend/alembic.ini を読み、接続先だけを差し替えた設定を返す。"""
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("sqlalchemy.url", database_url)
    return config


def upgrade_head(database_url: str) -> None:
    command.upgrade(alembic_config(database_url), "head")


def downgrade_base(database_url: str) -> None:
    command.downgrade(alembic_config(database_url), "base")
