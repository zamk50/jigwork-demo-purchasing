"""誤りの応答の扱い(方式設計の「横断の方式」の「例外とログ」)。

- API の誤りは、HTTP の状態と `{"detail": "<文>"}` の JSON で返す。
- 本文の形の誤り(欄の欠け・型の違い・JSON として読めない本文)は、422 と共通の文で返す。
  送った値は、応答にもログにも出さない。
- 想定しない例外は 500 と共通の文で返し、中身(例外の文と経路)はログにだけ残す。
- HTTPException などの想定した誤りは、FastAPI の既定の扱いのまま返す。
"""

import logging
from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel

logger = logging.getLogger("app.errors")

# 画面共通規則の「メッセージの出し方」の、想定しない誤りの文
UNEXPECTED_ERROR_MESSAGE = "時間をおいてもう一度試してください"

# 本文の形の誤りの文。画面は送る前に欄を確かめるので、ふつうは画面には出ない
VALIDATION_ERROR_MESSAGE = "入力の形が正しくありません"


class ErrorResponse(BaseModel):
    """誤りの応答。"""

    detail: str


# ルーターに付ける、OpenAPI の 422 の形。FastAPI の既定の配列の形の代わりに、誤りの応答の形にする
VALIDATION_ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {422: {"model": ErrorResponse}}


async def handle_validation_error(request: Request, exc: Exception) -> JSONResponse:
    """本文の形の誤りを、422 と共通の文で返す。送った値は返さない。"""
    return JSONResponse(status_code=422, content=ErrorResponse(detail=VALIDATION_ERROR_MESSAGE).model_dump())


async def handle_unexpected_error(request: Request, exc: Exception) -> JSONResponse:
    """想定しない例外をログに残し、500 と共通の文を返す。"""
    logger.error("想定しない例外: %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse(status_code=500, content=ErrorResponse(detail=UNEXPECTED_ERROR_MESSAGE).model_dump())


def install_error_handlers(app: FastAPI) -> None:
    """本文の形の誤りと想定しない例外の扱いをアプリに付ける。"""
    app.add_exception_handler(RequestValidationError, handle_validation_error)
    app.add_exception_handler(Exception, handle_unexpected_error)
