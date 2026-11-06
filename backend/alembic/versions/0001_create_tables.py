"""部署・役割・利用者・利用者の役割・ログインの状態のテーブルを作る

Revision ID: 0001
Revises:
Create Date: 2026-11-07
"""

from collections.abc import Sequence

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
