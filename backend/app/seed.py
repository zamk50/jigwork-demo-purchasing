"""初期データの 4 利用者を入れるコマンド(方式設計の「初期データ」の節。決定 D-04)。

使い方(backend/ で。先に `alembic upgrade head` で部署と役割を入れておく):

    python -m app.seed

DB の接続先 DATABASE_URL と、4 利用者のパスワード SEED_PASSWORD_* を環境変数(または backend/.env)から読む。
どれかが無いか空なら、DB に触れずに止まる(NFR-006)。
何度流しても同じ結果になる。社員番号が同じ利用者は作り直さず、氏名・部署・役割・パスワードを合わせる。
"""

import sys
from dataclasses import dataclass

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from pydantic import SecretStr, ValidationError, field_validator
from sqlalchemy import create_engine, delete, select
from sqlalchemy.orm import Session

from app.db.models import Department, Role, User, UserRole
from app.db.settings import DatabaseSettings


@dataclass(frozen=True)
class SeedUser:
    """初期データの利用者 1 人。env_var はパスワードを読む環境変数の名前。"""

    employee_no: str
    name: str
    department: str
    roles: tuple[str, ...]
    env_var: str


SEED_USERS = (
    SeedUser("000001", "社員 一郎", "営業部", ("employee",), "SEED_PASSWORD_EMPLOYEE"),
    SeedUser("000002", "上長 二郎", "営業部", ("employee", "manager"), "SEED_PASSWORD_MANAGER"),
    SeedUser("000003", "購買 三子", "総務部", ("buyer",), "SEED_PASSWORD_BUYER"),
    SeedUser("000004", "管理 四郎", "総務部", ("admin",), "SEED_PASSWORD_ADMIN"),
)


class SeedError(Exception):
    """初期データを入れられない(移行がまだ等)。"""


class SeedSettings(DatabaseSettings):
    """初期データのコマンドの設定。パスワードは値を出力に出さないよう SecretStr で持つ。"""

    seed_password_employee: SecretStr
    seed_password_manager: SecretStr
    seed_password_buyer: SecretStr
    seed_password_admin: SecretStr

    @field_validator(
        "database_url", "seed_password_employee", "seed_password_manager", "seed_password_buyer", "seed_password_admin"
    )
    @classmethod
    def _not_empty(cls, value: str | SecretStr) -> str | SecretStr:
        text = value.get_secret_value() if isinstance(value, SecretStr) else value
        if not text:
            raise ValueError("空である")
        return value

    def passwords(self) -> dict[str, str]:
        """パスワードの環境変数の名前 → 値。"""
        return {
            "SEED_PASSWORD_EMPLOYEE": self.seed_password_employee.get_secret_value(),
            "SEED_PASSWORD_MANAGER": self.seed_password_manager.get_secret_value(),
            "SEED_PASSWORD_BUYER": self.seed_password_buyer.get_secret_value(),
            "SEED_PASSWORD_ADMIN": self.seed_password_admin.get_secret_value(),
        }


def _password_matches(hasher: PasswordHasher, password_hash: str, password: str) -> bool:
    """今のハッシュがそのパスワードのもので、今の強さで作られているか。"""
    try:
        hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False
    return not hasher.check_needs_rehash(password_hash)


def seed_users(session: Session, passwords: dict[str, str], hasher: PasswordHasher) -> None:
    """4 利用者を入れるか、入っていれば氏名・部署・役割・パスワードを合わせる。"""
    departments = {d.name: d.id for d in session.scalars(select(Department))}
    role_codes = set(session.scalars(select(Role.code)))
    for spec in SEED_USERS:
        department_id = departments.get(spec.department)
        if department_id is None:
            raise SeedError(f"部署「{spec.department}」が無い。先に移行(alembic upgrade head)を流す")
        unknown_roles = set(spec.roles) - role_codes
        if unknown_roles:
            raise SeedError(f"役割 {sorted(unknown_roles)} が無い。先に移行(alembic upgrade head)を流す")

        password = passwords[spec.env_var]
        user = session.scalar(select(User).where(User.employee_no == spec.employee_no))
        if user is None:
            user = User(
                employee_no=spec.employee_no,
                name=spec.name,
                department_id=department_id,
                password_hash=hasher.hash(password),
            )
            session.add(user)
            session.flush()
        else:
            if user.name != spec.name:
                user.name = spec.name
            if user.department_id != department_id:
                user.department_id = department_id
            if not _password_matches(hasher, user.password_hash, password):
                user.password_hash = hasher.hash(password)

        wanted = set(spec.roles)
        current = set(session.scalars(select(UserRole.role_code).where(UserRole.user_id == user.id)))
        extra = current - wanted
        if extra:
            session.execute(delete(UserRole).where(UserRole.user_id == user.id, UserRole.role_code.in_(extra)))
        session.add_all(UserRole(user_id=user.id, role_code=code) for code in sorted(wanted - current))
    session.flush()


def _missing_variables(error: ValidationError) -> list[str]:
    return sorted({str(e["loc"][0]).upper() for e in error.errors() if e["loc"]})


def main() -> int:
    """設定を読み、4 利用者を 1 つのトランザクションで入れる。成功なら 0、止まれば 1 を返す。"""
    try:
        settings = SeedSettings()  # pyright: ignore[reportCallIssue]
    except ValidationError as e:
        names = "、".join(_missing_variables(e))
        print(f"初期データを入れられない。次の環境変数が無いか空である: {names}", file=sys.stderr)
        return 1

    engine = create_engine(settings.database_url)
    try:
        with Session(engine) as session, session.begin():
            seed_users(session, settings.passwords(), PasswordHasher())
    except SeedError as e:
        print(f"初期データを入れられない。{e}", file=sys.stderr)
        return 1
    finally:
        engine.dispose()

    print(f"初期データの {len(SEED_USERS)} 利用者を入れた。")
    return 0


if __name__ == "__main__":
    sys.exit(main())
