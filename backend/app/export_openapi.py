"""API の OpenAPI の JSON を標準出力に書き出す(方式設計の「技術の選定」: API の型は OpenAPI から生成する)。

使い方(backend/ で):

    .venv/bin/python -m app.export_openapi > ../frontend/openapi.json

create_app でアプリを組み、その OpenAPI を書き出す。DB には繋がないので、接続先は SQLite のメモリの URL にする。
ログインの状態の鍵は、書き出しにしか使わない使い捨ての乱数にする。
"""

import json
import secrets
import sys

from pydantic import SecretStr

from app.main import create_app
from app.settings import AppSettings


def build_openapi() -> dict[str, object]:
    """アプリの OpenAPI を返す。"""
    settings = AppSettings(database_url="sqlite://", session_secret=SecretStr(secrets.token_urlsafe(48)))
    return create_app(settings=settings).openapi()


def main() -> None:
    """OpenAPI の JSON を、キーの順をそろえて標準出力に書く。"""
    json.dump(build_openapi(), sys.stdout, ensure_ascii=False, indent=2, sort_keys=True)
    sys.stdout.write("\n")


if __name__ == "__main__":
    main()
