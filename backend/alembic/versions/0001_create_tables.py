"""部署・役割・利用者・利用者の役割・ログインの状態のテーブルを作る

部署と役割の行もここで入れる。秘密を含まないためである(決定 D-04)。
4 利用者は、パスワードを環境変数から読むので、初期データのコマンド(python -m app.seed)で入れる。
戻すと 5 つのテーブルを消す(方式設計の「戻し方」)。

Revision ID: 0001
Revises:
Create Date: 2026-11-07
"""

from collections.abc import Sequence

import sqlalchemy as sa

from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

DEPARTMENTS = ["総務部", "営業部", "製造部"]

ROLES = [
    {"code": "employee", "name": "社員", "sort_order": 1},
    {"code": "manager", "name": "上長", "sort_order": 2},
    {"code": "buyer", "name": "購買担当", "sort_order": 3},
    {"code": "admin", "name": "管理者", "sort_order": 4},
]


def _timestamp(name: str, comment: str, *, nullable: bool = False) -> sa.Column[sa.DateTime]:
    default = None if nullable else sa.func.now()
    return sa.Column(name, sa.DateTime(timezone=True), nullable=nullable, server_default=default, comment=comment)


def upgrade() -> None:
    departments = op.create_table(
        "departments",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False, comment="部署 ID"),
        sa.Column("name", sa.String(50), nullable=False, comment="部署名"),
        sa.PrimaryKeyConstraint("id", name="pk_departments"),
        sa.UniqueConstraint("name", name="uq_departments_name"),
        comment="T001 部署",
    )
    roles = op.create_table(
        "roles",
        sa.Column("code", sa.String(20), nullable=False, comment="役割コード"),
        sa.Column("name", sa.String(50), nullable=False, comment="役割名"),
        sa.Column("sort_order", sa.Integer(), nullable=False, comment="並び順"),
        sa.PrimaryKeyConstraint("code", name="pk_roles"),
        comment="T002 役割",
    )
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), sa.Identity(), nullable=False, comment="利用者 ID"),
        sa.Column("employee_no", sa.String(6), nullable=False, comment="社員番号"),
        sa.Column("name", sa.String(100), nullable=False, comment="氏名"),
        sa.Column("department_id", sa.Integer(), nullable=False, comment="部署 ID"),
        sa.Column("password_hash", sa.String(255), nullable=False, comment="パスワードのハッシュ"),
        sa.Column("failed_login_count", sa.Integer(), nullable=False, server_default="0", comment="誤った回数"),
        _timestamp("locked_until", "ロックの終わる時刻", nullable=True),
        _timestamp("created_at", "作った時刻"),
        _timestamp("updated_at", "直した時刻"),
        sa.PrimaryKeyConstraint("id", name="pk_users"),
        sa.UniqueConstraint("employee_no", name="uq_users_employee_no"),
        sa.ForeignKeyConstraint(["department_id"], ["departments.id"], name="fk_users_department_id_departments"),
        sa.CheckConstraint("employee_no ~ '^[0-9]{6}$'", name="ck_users_employee_no_6_digits"),
        comment="T003 利用者",
    )
    op.create_table(
        "user_roles",
        sa.Column("user_id", sa.Integer(), nullable=False, comment="利用者 ID"),
        sa.Column("role_code", sa.String(20), nullable=False, comment="役割コード"),
        sa.PrimaryKeyConstraint("user_id", "role_code", name="pk_user_roles"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_user_roles_user_id_users", ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["role_code"], ["roles.code"], name="fk_user_roles_role_code_roles"),
        comment="T004 利用者の役割",
    )
    op.create_table(
        "sessions",
        sa.Column("token_hash", sa.String(64), nullable=False, comment="印のハッシュ"),
        sa.Column("user_id", sa.Integer(), nullable=False, comment="利用者 ID"),
        _timestamp("created_at", "ログインした時刻"),
        _timestamp("last_seen_at", "最後の操作の時刻"),
        sa.PrimaryKeyConstraint("token_hash", name="pk_sessions"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], name="fk_sessions_user_id_users", ondelete="CASCADE"),
        comment="T005 ログインの状態",
    )

    op.bulk_insert(departments, [{"name": name} for name in DEPARTMENTS])
    op.bulk_insert(roles, ROLES)


def downgrade() -> None:
    op.drop_table("sessions")
    op.drop_table("user_roles")
    op.drop_table("users")
    op.drop_table("roles")
    op.drop_table("departments")
