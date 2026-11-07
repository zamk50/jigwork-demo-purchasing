"""#38/TC-19: Ruff・pyright(strict)・tsc・Oxlint の指摘が 0 件である。

型の検査と lint は jig のテストの手順に直接は書けないので、pytest のテストから流す。
jig gate の包みの中では backend/.venv/bin と frontend/node_modules/.bin が PATH に無いため、道具はパスで呼ぶ。
"""

import subprocess
import sys
from pathlib import Path

import pytest

BACKEND = Path(__file__).resolve().parents[1]
FRONTEND = BACKEND.parent / "frontend"
VENV_BIN = Path(sys.executable).parent
NODE_BIN = FRONTEND / "node_modules" / ".bin"

CHECKS: dict[str, tuple[Path, list[str]]] = {
    "ruff-lint": (BACKEND, [str(VENV_BIN / "ruff"), "check", "--no-cache", "."]),
    "ruff-format": (BACKEND, [str(VENV_BIN / "ruff"), "format", "--check", "--no-cache", "."]),
    "pyright": (BACKEND, [str(NODE_BIN / "pyright"), "--warnings", "--pythonpath", sys.executable]),
    "tsc": (FRONTEND, [str(NODE_BIN / "tsc"), "--noEmit", "-p", "tsconfig.json"]),
    "oxlint": (FRONTEND, [str(NODE_BIN / "oxlint"), "--deny-warnings", "src", "vite.config.ts"]),
}


@pytest.mark.parametrize("name", list(CHECKS))
def test_i38_tc19_checker_reports_no_findings(name: str) -> None:
    cwd, args = CHECKS[name]
    result = subprocess.run(args, cwd=cwd, capture_output=True, text=True, timeout=600, check=False)
    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, f"{name} の指摘がある(終了コード {result.returncode}):\n{output}"
