"""テストから API のサーバーを起動する役。

サーバーは別のプロセスで uvicorn から起動し、環境変数をテストが決めたものだけにする。
作業のディレクトリは一時のものにし、手元の backend/.env を読ませない。
"""

import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]


def start_api_server(variables: Mapping[str, str], cwd: Path, timeout: float = 60) -> subprocess.CompletedProcess[str]:
    """`uvicorn app.main:create_app --factory` で起動し、止まれば終了コードと出力を返す。

    起動できてしまうとサーバーは止まらないので、timeout で subprocess.TimeoutExpired になる。
    """
    env = {"PYTHONPATH": str(BACKEND), **variables}
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "uvicorn",
            "app.main:create_app",
            "--factory",
            "--host",
            "127.0.0.1",
            "--port",
            "0",
        ],
        cwd=cwd,
        env=env,
        capture_output=True,
        text=True,
        timeout=timeout,
        check=False,
    )
