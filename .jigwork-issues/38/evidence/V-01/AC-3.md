# 受入基準「役割による出し分け」(AC-3) 判定: 合格

## 何を・どう確かめたか

- 実行: `jig gate`(失敗 0 件。[gate-run.json](gate-run.json))で次が通った。
  - API「メニューは役割の行だけ」(TC-05) `backend/tests/test_i38_tc05_menu.py`
  - 画面の単体「役割の見出しごとに並べ、準備中は押せない」(TC-14) `frontend/src/pages/MenuPage.test.tsx`(手元の vitest でも通過)
  - 通しのテスト(TC-15): 役割の見出し(h2)と region の数が持つ役割の数と一致し、各 region の listitem の数が項目表の行の数と一致する。ほかの役割の項目が画面に出れば数が合わず落ちる。
- コード: `backend/app/menu/service.py` の build_menu は、利用者の持つ役割の行だけを項目表の順に組み立てる。ほかの役割の項目は作らない。
- 突き合わせ: 項目表 FR-016(`docs/requirements/functions/FNC-003.md`)と MENU_TABLE が一致。
