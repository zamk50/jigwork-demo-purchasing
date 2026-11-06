"""ログの出し方(方式設計の「横断の方式」の「例外とログ」)。

ログは標準出力に出す。ログインの成否と社員番号は残し、パスワードとログインの状態の印は残さない。
アプリのロガーは "app" の下に置く(例 app.auth)。
"""

import logging
import sys

APP_LOGGER = "app"


class _StdoutHandler(logging.Handler):
    """書くたびに今の標準出力へ出す(起動の後に標準出力が差し替わっても、そちらへ出す)。"""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            sys.stdout.write(f"{self.format(record)}\n")
            sys.stdout.flush()
        except Exception:
            self.handleError(record)


_STDOUT_HANDLER = _StdoutHandler()
_STDOUT_HANDLER.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s %(message)s"))


def configure_logging() -> None:
    """アプリのロガーが標準出力に INFO 以上を出すようにする。何度呼んでも 1 つだけ付ける。"""
    logger = logging.getLogger(APP_LOGGER)
    if logger.level == logging.NOTSET:
        logger.setLevel(logging.INFO)
    if _STDOUT_HANDLER not in logger.handlers:
        logger.addHandler(_STDOUT_HANDLER)
