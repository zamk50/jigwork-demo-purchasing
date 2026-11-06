"""想定しない例外の扱い(方式設計の「横断の方式」の「例外とログ」)。

想定しない例外は 500 と共通の文で返し、中身(例外の文と経路)はログにだけ残す。
HTTPException などの想定した誤りは、FastAPI の既定の扱いのまま返す。
"""

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("app.errors")

# 画面共通規則の「メッセージの出し方」の、想定しない誤りの文
UNEXPECTED_ERROR_MESSAGE = "時間をおいてもう一度試してください"


async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """想定しない例外をログに残し、500 と共通の文を返す。"""
    logger.error("想定しない例外: %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(status_code=500, content={"detail": UNEXPECTED_ERROR_MESSAGE})


def install_error_handlers(app: FastAPI) -> None:
    """想定しない例外の扱いをアプリに付ける。"""
    app.add_exception_handler(Exception, handle_unexpected_error)
