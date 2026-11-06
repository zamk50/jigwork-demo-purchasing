"""テストから初期データのコマンドを流す役。

コマンドは別のプロセスで流し、環境変数をテストが決めたものだけにする。
作業のディレクトリは一時のものにし、手元の backend/.env を読ませない。
"""

import secrets
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]

SEED_PASSWORD_VARIABLES = (
    "SEED_PASSWORD_EMPLOYEE",
    "SEED_PASSWORD_MANAGER",
    "SEED_PASSWORD_BUYER",
    "SEED_PASSWORD_ADMIN",
)


def random_seed_passwords() -> dict[str, str]:
    """4 利用者のパスワードの環境変数を、そのたびに作る乱数で返す。"""
    return {name: secrets.token_urlsafe(16) for name in SEED_PASSWORD_VARIABLES}


def run_seed(database_url: str | None, variables: Mapping[str, str], cwd: Path) -> subprocess.CompletedProcess[str]:
    """`python -m app.seed` を流し、終了コードと出力を返す。"""
    env = {"PYTHONPATH": str(BACKEND), **variables}
    if database_url is not None:
        env["DATABASE_URL"] = database_url
    return subprocess.run(
        [sys.executable, "-m", "app.seed"],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=300,
        check=False,
    )
