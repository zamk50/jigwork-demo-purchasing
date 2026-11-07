# 受入基準「テストと検査」(AC-8) 判定: 合格

- 手順 `.jigwork-test.json`: test に pytest(backend)・vitest(frontend)・Playwright(frontend)の 3 つがある。
- `jig gate`: 2 回走り、どちらも ok。テスト 152 件・失敗 0 件・止める項目 0 件。手順 5 件(入れ直し 2・テスト 3)すべて終了コード 0([gate-run.json](gate-run.json))。
  - 止める重さの項目(テストの集め方の変更 W8 `backend/pyproject.toml`、検査の設定の追加 G2 `frontend/.oxlintrc.json`・`frontend/tsconfig.json`、手順の新設 T1 `.jigwork-test.json`)はすべて passed: true(人が通した印)。
- `jig check`: 「テスト(G7 の包み) 緑(コミット 04554da6c4、手順 5 件のうち失敗 0 件、止める 0 件)」。
- 検査(TC-19) `backend/tests/test_i38_tc19_checks.py`・`test_i38_tc19_e2e_lint.py`: Ruff の lint と整形・pyright(`backend/pyproject.toml` で typeCheckingMode = "strict")・tsc・Oxlint(src と e2e)。検証役の手元の pytest でも 6 件すべて PASSED([pytest-local-sandbox.log](pytest-local-sandbox.log))。
- 補足: 手元の pytest は DB が立たず 105 件が setup の ERROR(サンドボックスで Unix ソケットを作れない。製品の不具合ではない)。DB を要るテストの合否は jig gate の結果に頼った。
