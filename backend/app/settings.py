"""API のサーバーの設定(方式設計の「設定」の節。NFR-006・NFR-007)。骨組み。"""

from collections.abc import Mapping

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class SettingsError(Exception):
    """要る設定が無いか正しくない。names は環境変数の名前の一覧。"""

    def __init__(self, names: list[str]) -> None:
        self.names = names
        super().__init__("、".join(names))


class AppSettings(BaseSettings):
    """API のサーバーの設定。"""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str
    session_secret: SecretStr
    cookie_secure: bool = True


def load_settings(environ: Mapping[str, str] | None = None) -> AppSettings:
    """設定を読む。"""
    raise NotImplementedError
