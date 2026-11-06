"""設定の読み込み(方式設計の「設定」の節。NFR-006・NFR-007)。

設定は環境変数から読む。手元では backend/.env に書いてもよい(このファイルはリポジトリに入れない)。
API のサーバーは起動の時に load_settings で読み、DB の接続先かログインの状態の鍵が無ければ止まる。
止まる時の文には環境変数の名前だけを出し、値は出さない。
"""

from collections.abc import Mapping

from pydantic import BaseModel, ConfigDict, SecretStr, ValidationError, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# ログインの状態の印をハッシュにする鍵の長さの下限(バイト)
SESSION_SECRET_MIN_BYTES = 32

_ENV_CONFIG = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


class SettingsError(Exception):
    """要る設定が無いか正しくない。names は、無いか正しくない環境変数の名前の一覧。"""

    def __init__(self, names: list[str]) -> None:
        self.names = names
        super().__init__(f"API のサーバーを起動できない。次の環境変数が無いか正しくない: {'、'.join(names)}")


def _require_text(value: str) -> str:
    if not value.strip():
        raise ValueError("空である")
    return value


class AppSettings(BaseModel):
    """API のサーバーの設定。鍵は値を出力に出さないよう SecretStr で持つ。"""

    model_config = ConfigDict(frozen=True, extra="ignore")

    database_url: str
    """DB の接続先。SQLAlchemy の URL(例 postgresql+psycopg://...)で書く。"""
    session_secret: SecretStr
    """ログインの状態の印をハッシュ(HMAC-SHA256)にする鍵。32 バイト以上。"""
    cookie_secure: bool = True
    """クッキーに Secure を付けるか。無いときは付ける(本番の既定)。"""

    @field_validator("database_url")
    @classmethod
    def _database_url_not_empty(cls, value: str) -> str:
        return _require_text(value)

    @field_validator("session_secret")
    @classmethod
    def _session_secret_long_enough(cls, value: SecretStr) -> SecretStr:
        if len(value.get_secret_value().encode("utf-8")) < SESSION_SECRET_MIN_BYTES:
            raise ValueError(f"{SESSION_SECRET_MIN_BYTES} バイト以上にする")
        return value


class _AppEnvironment(BaseSettings):
    """環境変数と .env から、AppSettings の値を文字列のまま集める。確かめは AppSettings で行う。"""

    model_config = _ENV_CONFIG

    database_url: str | None = None
    session_secret: str | None = None
    cookie_secure: str | None = None


def _variable_names(error: ValidationError) -> list[str]:
    return sorted({str(e["loc"][0]).upper() for e in error.errors() if e["loc"]})


def load_settings(environ: Mapping[str, str] | None = None) -> AppSettings:
    """設定を読む。欠けているか正しくなければ SettingsError で止まる。

    environ を渡せば、それだけから読む(テストで環境変数の代わりに使う)。
    渡さなければ、環境変数と、作業のディレクトリの .env から読む。
    """
    values: Mapping[str, object]
    if environ is None:
        values = _AppEnvironment().model_dump(exclude_none=True)
    else:
        lowered = {name.lower(): value for name, value in environ.items()}
        values = {name: lowered[name] for name in AppSettings.model_fields if name in lowered}
    try:
        return AppSettings.model_validate(values)
    except ValidationError as error:
        # ValidationError の文には入力の値(鍵)が入るので、つなげずに名前だけを出す
        raise SettingsError(_variable_names(error)) from None


class DatabaseSettings(BaseSettings):
    """DB の接続先だけの設定。移行(Alembic)と初期データのコマンドが使う。"""

    model_config = _ENV_CONFIG

    database_url: str

    @field_validator("database_url")
    @classmethod
    def _database_url_not_empty(cls, value: str) -> str:
        return _require_text(value)


def load_database_url() -> str:
    """環境変数か .env から DB の接続先を読む。無ければ pydantic の ValidationError で止まる。"""
    settings = DatabaseSettings()  # pyright: ignore[reportCallIssue]
    return settings.database_url
