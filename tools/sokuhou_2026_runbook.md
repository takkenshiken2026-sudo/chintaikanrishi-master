# 令和8年度(2026年) 解答速報 自動反映 手順書（runbook）

このファイルは、**試験当日(2026/11/15)の自動クロール用に起動されたセッションが読む作業手順**です。
目的は「TACの解答速報を取得し、公開されていれば当サイトの2026年解答速報ページに反映した**下書き**を用意して通知する」こと。
**公開（マージ）は人間が確認してから行う**ので、このセッションはマージもPR作成もしない。

---

## 前提・対象

- クロール元（唯一の取得先）: `https://www.tac-school.co.jp/kouza_chintai/sokuhou.html`
  - このホストは専用環境 `chintaikanrishi-sokuhou` で許可済み。`curl -sS` で取得できる（プロキシ設定済み）。
- 反映先ページ: `kaitou-sokuhou/2026/index.html`
- 試験: 2026/11/15(日) 13:00〜15:00。TACは例年**試験当日の夜ごろ**（2025年実績で19:00）に正答番号を公開。
- TACページの解答表は `<div class="cell question">問N</div><div class="cell answer">X</div>` という構造。
  公開前は X が「ー」。公開後に 1〜4（まれに没問/複数正解の表記）が入る。

## このセッションがやること（手順）

1. リポジトリ最新を取得。
   ```bash
   cd <repo>
   git fetch origin
   ```

2. **取得状況を確認**する。
   ```bash
   python3 tools/sokuhou_2026_update.py --check
   ```
   - 終了コード `2`（NOT PUBLISHED / 未公開）の場合 → **何も変更しない。**
     「まだ未公開（問○/50に番号あり）」とだけ短く報告してこのセッションを終える（通知は控えめに）。
   - 終了コード `0`（PUBLISHED / 公開済み）の場合 → 次へ。
   - 終了コード `4`（FETCH FAILED）の場合 → 取得失敗。ネットワーク/プロキシを確認し、
     それでも駄目ならその旨を通知して終える。

3. **既に反映済みか確認**。
   `kaitou-sokuhou/2026/index.html` の `id="sokuhou-answers"` が既に `[{...}]`（空でない）なら
   前の回で反映済み。TAC側の **更新（訂正）有無** を確認し、
   - 変化なし → 何もせず「反映済み・変化なし」と短く報告して終える。
   - TAC側が更新されていて内容が変わっている → 差分を人間に委ねる（上書きはせず通知のみ）。

4. **反映（下書き作成）**。未反映かつ公開済みなら:
   ```bash
   python3 tools/sokuhou_2026_update.py --apply
   ```
   - これで `kaitou-sokuhou/2026/index.html` の「解答一覧」欄に表が入り、
     `sokuhou-answers` JSON が埋まり、自己採点が有効化され、最終更新日が今日になる。
   - `tools/snapshots/` にTACのスナップショットが保存される（gitignore済み・コミットしない）。
   - 終了コード `3` や出力に `REVIEW REQUIRED` が出たら、**没問・複数正解・未公開の問が混在**している。
     その問番号を必ず通知に明記する（自動では全員正解扱いの暫定処理になっているため人間の確認が必須）。

5. **自己点検**（反映が正しいか目視）。
   ```bash
   git --no-pager diff -- kaitou-sokuhou/2026/index.html | head -80
   python3 -c "import re,json;t=open('kaitou-sokuhou/2026/index.html',encoding='utf-8').read();d=json.loads(re.search(r'id=\"sokuhou-answers\">(.*?)</script>',t,re.S).group(1));print('records',len(d));print([x['correct'] for x in d])"
   ```
   - `--check` の出力で表示された「正答(生値)」と、ページに入った数字が一致しているか確認する。
   - 50件そろっているか、JSONがパースできるか確認する。

6. **下書きブランチにコミット＆push**（マージはしない）。
   `--apply` で作業ツリーの `kaitou-sokuhou/2026/index.html` は既に書き換わっている。
   **その変更を保ったまま**新しいブランチを作る（`-b`。`origin/main`等へ切り直して変更を破棄しないこと）:
   ```bash
   git checkout -b claude/sokuhou-2026-answers   # 現在のHEAD(ツールのある開発ブランチ)から分岐。変更は保持される
   git add kaitou-sokuhou/2026/index.html
   git commit    # メッセージ例は下記。末尾に各セッション所定の属性行を付ける
   git push -u origin claude/sokuhou-2026-answers
   ```
   - 既に `claude/sokuhou-2026-answers` がある場合は `git checkout claude/sokuhou-2026-answers` で切替えてから add/commit。
   - もし環境が別の開発ブランチを強制する場合は、そのブランチにpushし、ブランチ名を通知に明記する。
   - コミットメッセージ例:
     ```
     feat: 令和8年度(2026年)解答速報をTAC速報ベースで反映（下書き・要確認）

     TAC解答速報 https://www.tac-school.co.jp/kouza_chintai/sokuhou.html を基に
     kaitou-sokuhou/2026/index.html の解答一覧・自己採点JSONを更新。
     公式正解ではなく参考解答。公開(マージ)前に人間が内容確認すること。
     ```

7. **通知**（これが「下書き＋通知」の通知部分）。次を分かりやすく報告する:
   - 「TACが公開 → 下書きを用意した」こと。
   - push先ブランチ名。
   - 取得した50問の正答番号（または `--check` 出力）。
   - TACの「更新日時」。
   - **要確認の問**（没問・複数正解・未公開があれば問番号を明記）。
   - 「公開するには人間がブランチを確認してマージ」する旨。

## やってはいけないこと

- `main`（デフォルトブランチ）への直接push、マージ、PR作成、PRのマージ。→ 公開は人間が行う。
- TACの生HTMLのコミット（著作物。`tools/snapshots/` はgitignore済み）。
- 没問・複数正解を確認なしで確定公開すること。必ず通知で人間に委ねる。
- 合格ライン（`data-pass`）の勝手な変更。公式合格点は後日発表。TACの「合格推定点」は参考情報として通知に添えるだけ。

## 補足: 手動で反映したい場合

人間が手動で行う場合も同じスクリプトが使える:
```bash
python3 tools/sokuhou_2026_update.py --check   # 公開状況だけ確認
python3 tools/sokuhou_2026_update.py --apply   # 公開済みならページを書き換え（下書き）
```
反映後、`kaitou-sokuhou/2026/index.html` の差分を確認し、問題なければ通常のレビュー・公開フローでマージする。
