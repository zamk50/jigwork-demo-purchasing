# 受入基準「テストと検査」(AC-8) 判定: 合格

- 手順 `.jigwork-test.json`: test に pytest(backend)・vitest(frontend)・Playwright(frontend)の 3 つがある。V-01 から変わっていない。
- `jig gate`(V-02 で検証役が流した最後の実行): コミット 5e855a1、2026-11-08T04:42:24+09:00、ok。テスト 153 件・失敗 0 件・止める項目 0 件。手順 5 件(入れ直し 2・テスト 3)すべて終了コード 0([gate-run.json](gate-run.json))。
  - V-01 の 152 件から 1 件増えたのは、初期データのコマンドのテスト 1 件(c5cb602)の分。
  - 止める重さの項目はすべて passed: true(人が通した印): テストの集め方の変更(W8)`backend/pyproject.toml`、検査の設定の追加(G2)`frontend/.oxlintrc.json`・`frontend/tsconfig.json`、手順の新設(T1)`.jigwork-test.json`、そして V-02 で新しく出た「赤のコミットで触ったテストのファイルを後で変えた」(W13)`backend/tests/test_i38_tc11_seed_command.py`。
  - W13 は、テストを 1 件足しただけ(既存のテストの期待は変わっていない。`git show c5cb602` で足した行だけであることを確かめた)。
- 検査(TC-19) `backend/tests/test_i38_tc19_checks.py`・`test_i38_tc19_e2e_lint.py`: Ruff の lint と整形・pyright(strict)・tsc・Oxlint(src と e2e)の 6 件が、検証役の手元でも PASSED([pytest-local-sandbox-passed.log](pytest-local-sandbox-passed.log))。
- 手元の pytest は 19 件合格・106 件が setup の ERROR。ERROR の理由は `could not create Unix socket ... Operation not permitted`(サンドボックスの制約で、製品の不具合ではない)。DB の要るテストの合否は jig gate に頼った。
- テスト項目ごとの合否と、件数から推した限界: [tc-results.md](tc-results.md)。
