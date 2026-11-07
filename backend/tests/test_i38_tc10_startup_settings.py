"""#38/TC-10: DB の接続先かログインの状態の鍵が無いと、API のサーバーは起動の時に止まる(NFR-006・NFR-007)。

サーバーは別のプロセスで uvicorn から起動し、環境変数をテストが決めたものだけにする。
設定の読み込みは、環境変数の代わりに辞書を渡して確かめる。
"""

import secrets
from pathlib import Path

import pytest
from fastapi import FastAPI

from app.main import create_app
from app.settings import AppSettings, SettingsError, load_settings
from tests.serving import start_api_server

REQUIRED_VARIABLES = ("DATABASE_URL", "SESSION_SECRET")


def _complete_environ() -> dict[str, str]:
    """起動に要る設定をそろえた環境変数。接続先には起動の時に繋がないので、無い DB を指してよい。"""
    return {
        "DATABASE_URL": f"postgresql+psycopg://app@/db_{secrets.token_hex(4)}?host=/nonexistent",
        "SESSION_SECRET": secrets.token_urlsafe(32),
    }


@pytest.mark.parametrize("missing", REQUIRED_VARIABLES)
def test_i38_tc10_server_stops_at_startup_without_a_required_variable(tmp_path: Path, missing: str) -> None:
    environ = _complete_environ()
    del environ[missing]

    result = start_api_server(environ, tmp_path)

    assert result.returncode != 0
    assert missing in result.stderr, f"止まった理由に {missing} が出ていない:\n{result.stderr}"
    output = f"{result.stdout}\n{result.stderr}"
    assert all(value not in output for value in environ.values()), "設定の値が出力に出ている"


@pytest.mark.parametrize("empty", REQUIRED_VARIABLES)
def test_i38_tc10_server_stops_at_startup_with_an_empty_variable(tmp_path: Path, empty: str) -> None:
    environ = _complete_environ()
    environ[empty] = ""

    result = start_api_server(environ, tmp_path)

    assert result.returncode != 0
    assert empty in result.stderr, f"止まった理由に {empty} が出ていない:\n{result.stderr}"


def test_i38_tc10_server_stops_at_startup_with_a_short_session_secret(tmp_path: Path) -> None:
    environ = _complete_environ()
    short_secret = secrets.token_hex(15)  # 30 バイト。方式設計の「設定」の節は 32 バイト以上
    environ["SESSION_SECRET"] = short_secret

    result = start_api_server(environ, tmp_path)

    assert result.returncode != 0
    assert "SESSION_SECRET" in result.stderr, f"止まった理由に SESSION_SECRET が出ていない:\n{result.stderr}"
    output = f"{result.stdout}\n{result.stderr}"
    assert short_secret not in output, "ログインの状態の鍵が出力に出ている"


@pytest.mark.parametrize("missing", REQUIRED_VARIABLES)
def test_i38_tc10_load_settings_names_the_missing_variable(missing: str) -> None:
    environ = _complete_environ()
    del environ[missing]

    with pytest.raises(SettingsError) as info:
        load_settings(environ)

    assert info.value.names == [missing]
    assert missing in str(info.value)


def test_i38_tc10_load_settings_names_both_missing_variables() -> None:
    with pytest.raises(SettingsError) as info:
        load_settings({})

    assert sorted(info.value.names) == sorted(REQUIRED_VARIABLES)


def test_i38_tc10_load_settings_reads_the_variables() -> None:
    environ = _complete_environ()

    settings = load_settings(environ)

    assert settings.database_url == environ["DATABASE_URL"]
    assert settings.session_secret.get_secret_value() == environ["SESSION_SECRET"]
    assert environ["SESSION_SECRET"] not in repr(settings), "ログインの状態の鍵が設定の表示に出ている"
    assert settings.cookie_secure is True, "COOKIE_SECURE が無いときは Secure を付ける(本番の既定)"


@pytest.mark.parametrize(("value", "expected"), [("false", False), ("true", True)])
def test_i38_tc10_load_settings_reads_cookie_secure(value: str, expected: bool) -> None:
    environ = {**_complete_environ(), "COOKIE_SECURE": value}

    settings = load_settings(environ)

    assert settings.cookie_secure is expected


def test_i38_tc10_app_is_built_from_complete_settings() -> None:
    settings = load_settings(_complete_environ())

    app = create_app(settings)

    assert isinstance(app, FastAPI)
    assert isinstance(settings, AppSettings)
