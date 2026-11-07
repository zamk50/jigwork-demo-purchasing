"""#38/TC-19: 画面の通しのテストのソースにも、Oxlint の指摘が 0 件である。

test_i38_tc19_checks.py の Oxlint は画面の本体(src と vite.config.ts)だけを見る。
ここでは、通しのテスト(e2e)と Playwright の設定(playwright.config.ts)を見る。
jig gate の包みの中では frontend/node_modules/.bin が PATH に無いため、道具はパスで呼ぶ。
"""

import subprocess
from pathlib import Path

BACKEND = Path(__file__).resolve().parents[1]
FRONTEND = BACKEND.parent / "frontend"
OXLINT = FRONTEND / "node_modules" / ".bin" / "oxlint"
TARGETS = ["e2e", "playwright.config.ts"]


def test_i38_tc19_oxlint_reports_no_findings_in_e2e_sources() -> None:
    for target in TARGETS:
        assert (FRONTEND / target).exists(), f"Oxlint の対象 {target} が frontend に無い"
    args = [str(OXLINT), "--deny-warnings", *TARGETS]
    result = subprocess.run(args, cwd=FRONTEND, capture_output=True, text=True, timeout=600, check=False)
    output = f"{result.stdout}\n{result.stderr}"
    assert result.returncode == 0, f"Oxlint の指摘がある(終了コード {result.returncode}):\n{output}"
