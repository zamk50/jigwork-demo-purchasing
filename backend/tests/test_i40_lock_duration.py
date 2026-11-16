"""#40/TC-08: ロックの時間は 30 分である(FR-003)。

ロックの振る舞いのテストはこの定数を参照するので、定数の値そのものをここで確かめる。
"""

from datetime import timedelta

from app.auth.service import LOCK_DURATION


def test_i40_tc08_lock_duration_is_30_minutes() -> None:
    assert LOCK_DURATION == timedelta(minutes=30)
