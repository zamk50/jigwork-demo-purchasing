"""差し替えられる時計(方式設計の「横断の方式」の節)。

ログインの状態の切れ(30 分・8 時間)とロック(15 分)は、この時計の今で判定する。
アプリは create_app(clock=...) で受け取り、テストでは進められる時計を渡す。
業務の層は Clock の形だけに頼り、FastAPI の型に頼らない。
"""

from datetime import UTC, datetime
from typing import Protocol


class Clock(Protocol):
    """今の時刻を返すもの。時刻は時差つき(UTC)で返す。"""

    def now(self) -> datetime: ...


class SystemClock:
    """本物の時計。"""

    def now(self) -> datetime:
        return datetime.now(UTC)
