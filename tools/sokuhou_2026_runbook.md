# 令和8年度(2026年) 解答速報 自動反映 手順書（runbook）

試験当日(2026/11/15)の自動クロール用に起動されたセッションが読む作業手順。
目的は「TACの解答速報＋他社判明分をマージし、当サイトの2026年解答速報ページに反映して
**逐次公開**する」こと。
**公開方針（2026/11/15 ユーザー決定）＝「判明次第 逐次公開」**：
devブランチ `claude/relaxed-hypatia-ib3g7g` に反映・コミット後、**mainへFF（早送り）マージして公開**する。
ただしFF不可（mainが別コミットで進んでいる）なら**公開は保留**して報告する（force push はしない）。PR作成はしない。

## マージ方針（問ごと）

1. TACが正答番号を公表していれば **TACを最優先**。
2. TAC未公表(ー)なら `kaitou-sokuhou/2026/answers-known.json` の**判明分**を使う（他社速報など）。
3. どちらも無ければ「ー」(保留)。

`answers-known.json` は人間（またはこのセッション）が他社速報の判明分を随時追記するファイル。
TACが埋まればTACが優先されるので、TAC公表後も残しておいて問題ない。

## 前提・対象

- クロール元: `https://www.tac-school.co.jp/kouza_chintai/sokuhou.html`（専用環境 `chintaikanrishi-sokuhou` で許可済み、`curl -sS`で取得可）
- 反映先: `kaitou-sokuhou/2026/index.html`
- 作業ブランチ: `claude/relaxed-hypatia-ib3g7g`（ツール・判明分・反映を全てここに置き、人間がmainへマージして公開）
- TACの解答表構造: `<div class="cell question">問N</div><div class="cell answer">X</div>`（未公表は「ー」）

## 手順

```bash
cd <repo>
git fetch origin
git checkout claude/relaxed-hypatia-ib3g7g
git pull --ff-only origin claude/relaxed-hypatia-ib3g7g
python3 tools/sokuhou_2026_update.py --apply
```

`--apply` の挙動（冪等・何度実行してもOK）:
- TAC＋`answers-known.json` をマージし、`kaitou-sokuhou/2026/index.html` の**解答一覧の表**を更新
  （判明は数字、未判明は「ー」）。
- **全50問が判明したときだけ**自己採点ツールを有効化（解答JSONを投入）。
  部分的な間は自己採点は「準備中」のまま（誤採点防止）。
- 最終更新日を今日に更新。
- `tools/snapshots/` にTACスナップショットを保存（gitignore済み・コミットしない）。
- 出力に `REVIEW REQUIRED` が出たら没問・複数正解・想定外値あり → 問番号を通知に明記。
- 終了コード: 0=反映あり / 2=判明ゼロ（何もしない）/ 4=取得失敗。

反映後、差分があればコミット＆push、続けてmainへFF公開（逐次公開）:
```bash
git --no-pager diff --stat
git add -A
git commit    # 末尾に各セッション所定の属性行(Co-Authored-By 等)を付ける
git push origin claude/relaxed-hypatia-ib3g7g
# ↓ 逐次公開（FF不可なら公開保留で報告。force push はしない）
git checkout main && git pull --ff-only origin main \
  && git merge --ff-only claude/relaxed-hypatia-ib3g7g \
  && git push origin main
git checkout claude/relaxed-hypatia-ib3g7g
```

## 通知で伝えること

- TACが公表した問数 / マージ後の判明問数（例: 「TAC 0問・判明 12/50」）。
- 変化があったか（新たに判明した問 など）。
- ※要確認の問（没問・複数正解・想定外値があれば問番号）。
- 全50問そろったら「自己採点を有効化した」こと。
- 公開（main反映）は人間が差分確認後に行う旨。

## やってはいけないこと

- `main` への **force push** や、FF不可時の強制マージ（その場合は公開保留で報告）。PR作成もしない。
- TACの生HTMLのコミット（著作物。`tools/snapshots/` はgitignore済み）。
- 没問・複数正解を確認なしで確定すること（通知で人間に委ねる）。
- 合格ライン（`data-pass`）の勝手な変更。TACの「合格推定点」は参考として通知に添えるだけ。

## 手動運用（人間 or このセッション）

他社速報で新たに判明した問があれば `kaitou-sokuhou/2026/answers-known.json` の `answers` に
`"問番号": 正答番号` を追記し、`--apply` を実行 → コミット＆push。
TACが本公開したら同じく `--apply` でTAC優先に自動で上書きされる。

```bash
python3 tools/sokuhou_2026_update.py --check   # 取得・マージ状況の確認だけ
python3 tools/sokuhou_2026_update.py --apply   # 反映（下書き）
```
