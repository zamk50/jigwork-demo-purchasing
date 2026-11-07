"""テストで進める時計。

ログインの状態の切れ(30 分・8 時間)とロック(15 分)を、待たずに確かめるために使う。
アプリには create_app(clock=...) で渡す。
"""

from datetime import datetime, timedelta


class ManualClock:
    """advance で進めるまで止まっている時計。時刻は時差つき(UTC)で持つ。"""

    def __init__(self, start: datetime) -> None:
        if start.tzinfo is None:
            raise ValueError("時計の始まりは時差つきの時刻で渡す")
        self._now = start

    def now(self) -> datetime:
        return self._now

    def advance(self, delta: timedelta) -> None:
        """時計を delta だけ進める。"""
        self._now += delta
