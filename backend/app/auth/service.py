"""ログインとログインの状態の業務の処理(方式設計の「認証と認可の方式」。決定 D-01・D-02)。

業務の層なので FastAPI の型に頼らない。DB のセッションと時計と照合の役を引数で受け取る。

- ログイン: 社員番号で利用者を引き、パスワードのハッシュを argon2id で照らす。
- 失敗の扱い(FR-002・FR-023・FR-024。決定 D-09): どの失敗でも argon2id の照合を 1 回だけ行ってから返す。
  - 数字 6 桁でない社員番号・登録のない社員番号・ロック中は、ダミーのハッシュと照らす。
  - 役割なしの判定は、照合の後に行う。
- ロック(FR-003・FR-004・FR-020。決定 D-08): 利用者の行を SELECT … FOR UPDATE で押さえてから数える。
  - 続けて 5 回誤ると、ロックの終わる時刻を今から 15 分後にする。
  - ロック中の試みは、正誤によらず列を変えない。
  - ロックの終わる時刻を過ぎた最初の試みで、回数を 0 に戻してから数える。成功したときも 0 に戻す。
- ログインの状態: 印ごとに 1 行を持つ。表に入れるのは印そのものではなく、鍵つきのハッシュ(HMAC-SHA256)である。
  - 最後の操作から 30 分を超えるか、ログインから 8 時間を超えると切れる(FR-005・FR-006)。
  - 切れた行は、引いた時に消す。ログインのたびに、表の中の切れた行をまとめて消す。
- ログアウト: その印の行を消す。行がなくても誤りにしない。
"""

import hashlib
import hmac
import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta

from argon2 import PasswordHasher
from argon2.exceptions import InvalidHashError, VerificationError
from sqlalchemy import delete, exists, or_, select
from sqlalchemy.orm import Session

from app.db.models import Department, LoginSession, Role, User, UserRole

# ログインの失敗の共通の文(FR-002)。どの失敗でも同じ文で返す
LOGIN_FAILED_MESSAGE = "社員番号かパスワードが違います"

# ログインの状態の印の乱数のバイト数
TOKEN_BYTES = 32

# 社員番号の桁数(FR-001。数字 6 桁)
EMPLOYEE_NO_LENGTH = 6

# 続けて誤るとロックする回数と、ロックの長さ(FR-003)
MAX_FAILED_LOGINS = 5
LOCK_DURATION = timedelta(minutes=15)

# ログインの状態の切れ方(FR-005・FR-006)。この長さを超えると切れる
IDLE_TIMEOUT = timedelta(minutes=30)
ABSOLUTE_TIMEOUT = timedelta(hours=8)


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


def make_dummy_password_hash(hasher: PasswordHasher) -> str:
    """照合の要らない失敗で照らすダミーのハッシュ。照合の役と同じ強さで、どのパスワードとも合わない乱数から作る。"""
    return hasher.hash(secrets.token_urlsafe(TOKEN_BYTES))


def is_well_formed_employee_no(employee_no: str) -> bool:
    """社員番号が数字(ASCII の 0〜9)6 桁か。"""
    return len(employee_no) == EMPLOYEE_NO_LENGTH and employee_no.isascii() and employee_no.isdigit()


def _has_roles(session: Session, user: User) -> bool:
    return bool(session.scalar(select(exists().where(UserRole.user_id == user.id))))


def authenticate(
    session: Session,
    hasher: PasswordHasher,
    dummy_password_hash: str,
    employee_no: str,
    password: str,
    now: datetime,
) -> User | None:
    """社員番号とパスワードが合い、ロック中でなく、役割を持つ利用者なら返す。そうでなければ None を返す。

    どの道筋でも照合を 1 回だけ行う(決定 D-09)。誤った回数とロックの列は、利用者の行を押さえてから変える(決定 D-08)。
    照合に通ったハッシュが今の強さより弱ければ、今の強さで作り直す。
    """
    if not is_well_formed_employee_no(employee_no):
        _password_matches(hasher, dummy_password_hash, password)
        return None

    user = session.scalar(select(User).where(User.employee_no == employee_no).with_for_update())
    if user is None:
        _password_matches(hasher, dummy_password_hash, password)
        return None

    if user.locked_until is not None:
        if now < user.locked_until:
            # ロック中は正誤によらず数えず、ロックも延ばさない(FR-020)
            _password_matches(hasher, dummy_password_hash, password)
            return None
        # ロックが終わった最初の試みで、回数を 0 に戻してから数える(FR-004)
        user.failed_login_count = 0
        user.locked_until = None

    if not _password_matches(hasher, user.password_hash, password):
        user.failed_login_count += 1
        if user.failed_login_count >= MAX_FAILED_LOGINS:
            user.locked_until = now + LOCK_DURATION
        return None

    if not _has_roles(session, user):
        # 役割を持たない利用者はログインできない(FR-023)。ログインの成功ではないので回数は変えない
        return None

    user.failed_login_count = 0
    if hasher.check_needs_rehash(user.password_hash):
        user.password_hash = hasher.hash(password)
    return user


def _is_expired(login_session: LoginSession, now: datetime) -> bool:
    return now - login_session.last_seen_at > IDLE_TIMEOUT or now - login_session.created_at > ABSOLUTE_TIMEOUT


def delete_expired_sessions(session: Session, now: datetime) -> None:
    """表の中の切れたログインの状態の行をまとめて消す。"""
    session.execute(
        delete(LoginSession).where(
            or_(LoginSession.last_seen_at < now - IDLE_TIMEOUT, LoginSession.created_at < now - ABSOLUTE_TIMEOUT)
        )
    )


def start_session(session: Session, user: User, token_hash: str, now: datetime) -> None:
    """ログインの状態の行を足す。ログインした時刻と最後の操作の時刻は now にする。"""
    session.add(LoginSession(token_hash=token_hash, user_id=user.id, created_at=now, last_seen_at=now))
    session.flush()


def resume_session(session: Session, token_hash: str, now: datetime) -> User | None:
    """印のハッシュでログインの状態を引き、有効なら最後の操作の時刻を now にして利用者を返す。

    切れていれば、その行を消して None を返す(FR-005・FR-006)。
    """
    login_session = session.get(LoginSession, token_hash)
    if login_session is None:
        return None
    if _is_expired(login_session, now):
        session.delete(login_session)
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
