"""SQLAlchemy のモデル(方式設計の「テーブル」の節)。

すべてのテーブルと列に、日本語の論理名のコメントを付ける(NFR-011)。
テーブルのコメントは「T001 部署」のように、テーブル番号と論理名を半角の空白でつなぐ(決定 D-06)。
表の形の正本は Alembic の移行(backend/alembic/versions/)で、このモデルはそれに合わせる。
"""

from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Identity, Integer, MetaData, String, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

# 制約の名前の付け方。移行で付ける名前と合わせる
NAMING_CONVENTION = {
    "pk": "pk_%(table_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "ix": "ix_%(column_0_label)s",
}

# 社員番号は数字 6 桁(FR-001)
EMPLOYEE_NO_PATTERN = "^[0-9]{6}$"


class Base(DeclarativeBase):
    """モデルの基底。"""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class Department(Base):
    """T001 部署。"""

    __tablename__ = "departments"
    __table_args__ = ({"comment": "T001 部署"},)

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True, comment="部署 ID")
    name: Mapped[str] = mapped_column(String(50), unique=True, comment="部署名")


class Role(Base):
    """T002 役割。"""

    __tablename__ = "roles"
    __table_args__ = ({"comment": "T002 役割"},)

    code: Mapped[str] = mapped_column(String(20), primary_key=True, comment="役割コード")
    name: Mapped[str] = mapped_column(String(50), comment="役割名")
    sort_order: Mapped[int] = mapped_column(Integer, comment="並び順")


class User(Base):
    """T003 利用者。パスワードは argon2id のハッシュだけを持つ(FR-010・NFR-005)。"""

    __tablename__ = "users"
    __table_args__ = (
        CheckConstraint(f"employee_no ~ '{EMPLOYEE_NO_PATTERN}'", name="employee_no_6_digits"),
        {"comment": "T003 利用者"},
    )

    id: Mapped[int] = mapped_column(Integer, Identity(), primary_key=True, comment="利用者 ID")
    employee_no: Mapped[str] = mapped_column(String(6), unique=True, comment="社員番号")
    name: Mapped[str] = mapped_column(String(100), comment="氏名")
    department_id: Mapped[int] = mapped_column(ForeignKey("departments.id"), comment="部署 ID")
    password_hash: Mapped[str] = mapped_column(String(255), comment="パスワードのハッシュ")
    failed_login_count: Mapped[int] = mapped_column(Integer, server_default="0", comment="誤った回数")
    locked_until: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), comment="ロックの終わる時刻")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="作った時刻"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="直した時刻"
    )


class UserRole(Base):
    """T004 利用者の役割。利用者 ID と役割コードの 2 つで主キー。"""

    __tablename__ = "user_roles"
    __table_args__ = ({"comment": "T004 利用者の役割"},)

    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), primary_key=True, comment="利用者 ID"
    )
    role_code: Mapped[str] = mapped_column(ForeignKey("roles.code"), primary_key=True, comment="役割コード")


class LoginSession(Base):
    """T005 ログインの状態。印そのものではなく、鍵つきのハッシュを持つ。"""

    __tablename__ = "sessions"
    __table_args__ = ({"comment": "T005 ログインの状態"},)

    token_hash: Mapped[str] = mapped_column(String(64), primary_key=True, comment="印のハッシュ")
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), comment="利用者 ID")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="ログインした時刻"
    )
    last_seen_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), comment="最後の操作の時刻"
    )
