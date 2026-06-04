# 試験ガイド「編集合格」全件リライト

**正本:** `~/Projects/exam-site-shell/docs/guide-expert-rewrite-program.md`

**本サイトのお手本**

- slug: `schedule-application`
- batch: `tools/chintai_rewrite_exemplar.py`

**5本 batch の手順:** `docs/guide-hand-rewrite-batch-workflow.md`（`exam-site-shell` から sync）

**運用:** 宅建 49/49 完走後に着手。現状 expert_pass **5/149**（exemplar + batch1 適用済み）。

| batch | 内容 |
|-------|------|
| exemplar | 日程・申込 `schedule-application` |
| 1 | 試験概要・学習計画・過去問・受験資格 |

```bash
cd ~/Projects/chintaikanrishi-master
python3 tools/validate_guide_hand_batch.py --batch tools/chintai_rewrite_batchN_expert.py
python3 tools/run_guide_hand_batch.py --batch tools/chintai_rewrite_batchN_expert.py
python3 tools/build_article_pages.py
```
