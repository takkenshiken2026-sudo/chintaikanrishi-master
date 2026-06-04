# 試験ガイド「編集合格」全件リライト

**正本:** `~/Projects/exam-site-shell/docs/guide-expert-rewrite-program.md`

**本サイトのお手本**

- slug: `schedule-application`
- batch: `tools/chintai_rewrite_exemplar.py`

**5本 batch の手順:** `docs/guide-hand-rewrite-batch-workflow.md`（`exam-site-shell` から sync）

**運用:** 宅建 49/49 完走後に着手。現状 expert_pass **70/149**（exemplar + batch1–14 適用済み）。

| batch | 内容 |
|-------|------|
| exemplar | 日程・申込 `schedule-application` |
| 1 | 試験概要・学習計画・過去問・受験資格 |
| 2 | 合格点・受験料・申込フロー・法令/契約ハブ |
| 3–4 | 設備ハブ・業法・原状回復・借地借家・設備税務・直前 |
| 5–6 | 合格後・重説・敷金・滞納・ADR・PM/保険・5問免除・一問一答 |
| 7–8 | 再受験・公式情報・初受験・資格比較・両立・締切・合格率 |
| 9–10 | 受験資格・5問免除・会場・試験形式・学習日程 |
| 11–12 | 時間配分・出題範囲・改定・難易度・合格率の読み方 |
| 13–14 | 学習計画（3/6/12ヶ月・社会人）・独学開始・失敗パターン |

```bash
cd ~/Projects/chintaikanrishi-master
python3 tools/validate_guide_hand_batch.py --batch tools/chintai_rewrite_batchN_expert.py
python3 tools/run_guide_hand_batch.py --batch tools/chintai_rewrite_batchN_expert.py
python3 tools/build_article_pages.py
```
