"""差し替えられる時計。骨組み。"""

from datetime import datetime
from typing import Protocol


class Clock(Protocol):
    """今の時刻を返すもの。"""

    def now(self) -> datetime: ...


class SystemClock:
    """本物の時計。"""

    def now(self) -> datetime:
        raise NotImplementedError
