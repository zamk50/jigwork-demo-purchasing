"""ログインとログインの状態の業務の処理(方式設計の「認証と認可の方式」。決定 D-01・D-02)。

業務の層なので FastAPI の型に頼らない。DB のセッションと時計と照合の役を引数で受け取る。

- ログイン: 社員番号で利用者を引き、パスワードのハッシュを argon2id で照らす。
- ログインの状態: 印ごとに 1 行を持つ。表に入れるのは印そのものではなく、鍵つきのハッシュ(HMAC-SHA256)である。
- ログアウト: その印の行を消す。行がなくても誤りにしない。
"""

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import Department, LoginSession, Role, User, UserRole

# ログインの失敗の共通の文(FR-002)。どの失敗でも同じ文で返す
LOGIN_FAILED_MESSAGE = "社員番号かパスワードが違います"

# ログインの状態の印の乱数のバイト数
TOKEN_BYTES = 32


@dataclass(frozen=True)
class RoleInfo:
    """利用者の持つ役割 1 つ。"""

    code: str
    name: str


@dataclass(frozen=True)
class LoginUser:
    """ログイン中の利用者。役割は役割の並び順に持つ。"""

    id: int
    employee_no: str
    name: str
    department: str
    roles: tuple[RoleInfo, ...]


def new_token() -> str:
    """ログインの状態の印を作る。クッキーに入れられる文字だけで、32 バイトの乱数を表す。"""
    return secrets.token_urlsafe(TOKEN_BYTES)


def hash_token(secret: str, token: str) -> str:
    """印の鍵つきのハッシュ(HMAC-SHA256 の 16 進。64 文字)。表にはこれだけを入れる。"""
    return hmac.new(secret.encode("utf-8"), token.encode("utf-8"), hashlib.sha256).hexdigest()


def _password_matches(hasher: PasswordHasher, password_hash: str, password: str) -> bool:
    try:
        hasher.verify(password_hash, password)
    except (VerificationError, InvalidHashError):
        return False
    return True


def authenticate(session: Session, hasher: PasswordHasher, employee_no: str, password: str) -> User | None:
    """社員番号とパスワードが合えば利用者を返す。合わなければ None を返す。

    照合に通ったハッシュが今の強さより弱ければ、今の強さで作り直す。
    """
    user = session.scalar(select(User).where(User.employee_no == employee_no))
    if user is None:
        return None
    if not _password_matches(hasher, user.password_hash, password):
        return None
    if hasher.check_needs_rehash(user.password_hash):
        user.password_hash = hasher.hash(password)
    return user


def start_session(session: Session, user: User, token_hash: str, now: datetime) -> None:
    """ログインの状態の行を足す。ログインした時刻と最後の操作の時刻は now にする。"""
    session.add(LoginSession(token_hash=token_hash, user_id=user.id, created_at=now, last_seen_at=now))
    session.flush()


def resume_session(session: Session, token_hash: str, now: datetime) -> User | None:
    """印のハッシュでログインの状態を引き、有効なら最後の操作の時刻を now にして利用者を返す。"""
    login_session = session.get(LoginSession, token_hash)
    if login_session is None:
        return None
    login_session.last_seen_at = now
    return session.get(User, login_session.user_id)


def end_session(session: Session, token_hash: str) -> None:
    """その印のログインの状態を消す。行がなくても誤りにしない。"""
    session.execute(delete(LoginSession).where(LoginSession.token_hash == token_hash))


def load_login_user(session: Session, user: User) -> LoginUser:
    """利用者の部署名と役割(役割の並び順)をそろえて返す。"""
    department = session.scalars(select(Department.name).where(Department.id == user.department_id)).one()
    roles = session.execute(
        select(Role.code, Role.name)
        .join(UserRole, UserRole.role_code == Role.code)
        .where(UserRole.user_id == user.id)
        .order_by(Role.sort_order)
    ).all()
    return LoginUser(
        id=user.id,
        employee_no=user.employee_no,
        name=user.name,
        department=department,
        roles=tuple(RoleInfo(code=code, name=name) for code, name in roles),
    )
