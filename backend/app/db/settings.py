"""DB の接続先の設定。

接続先は環境変数 DATABASE_URL から読む。手元では backend/.env に書いてもよい(NFR-006)。
"""

from pydantic_settings import BaseSettings, SettingsConfigDict


class DatabaseSettings(BaseSettings):
    """DB の接続先。SQLAlchemy の URL(例 postgresql+psycopg://...)で書く。"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str


def load_database_url() -> str:
    """環境変数か .env から DB の接続先を読む。無ければ pydantic の ValidationError で止まる。"""
    settings = DatabaseSettings()  # pyright: ignore[reportCallIssue]
    return settings.database_url
