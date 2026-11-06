"""テストから API を呼ぶ役。

Starlette の TestClient は、型の検査では httpx2 の Client を親に持つ(実行の時は httpx に戻る)。
依存にある httpx の型で検査できるよう、httpx.Client として返す。
with で使うと、アプリの起動と終わりの処理(lifespan)も流れる。
"""

from typing import cast

import httpx
from fastapi import FastAPI
from fastapi.testclient import TestClient


def api_client(app: FastAPI, *, raise_server_exceptions: bool = True) -> httpx.Client:
    """アプリを呼ぶクライアント。raise_server_exceptions=False なら、想定しない例外を 500 の応答で受ける。"""
    return cast(httpx.Client, TestClient(app, raise_server_exceptions=raise_server_exceptions))
