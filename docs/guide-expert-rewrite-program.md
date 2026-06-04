# 試験ガイド「編集合格」全件リライト

**正本:** `~/Projects/exam-site-shell/docs/guide-expert-rewrite-program.md`

**本サイトのお手本**

- slug: `schedule-application`
- batch: `tools/chintai_rewrite_exemplar.py`

**5本 batch の手順:** `docs/guide-hand-rewrite-batch-workflow.md`（`exam-site-shell` から sync）

**運用:** 宅建 49/49 完走後に着手。**149/149 完走**（buildable ガイド全件・exemplar + batch1–30）。

| 区分 | 内容 |
|------|------|
| exemplar | 日程・申込 `schedule-application` |
| batch1–20 | 概要・ハブ・学習・教材・過去問・用語 |
| batch21–25 | 復習・直前・当日・合格後・再受験 |
| batch26–30 | 制度更新・誤解・分野別 field-* シリーズ |

**未対象（別枠）:** アフィリエイト10本（ASP URL 未設定3本は HTML 未生成。リンク準備後に expert batch で対応）

```bash
cd ~/Projects/chintaikanrishi-master
python3 tools/validate_guide_hand_batch.py --batch tools/chintai_rewrite_batchN_expert.py
python3 tools/run_guide_hand_batch.py --batch tools/chintai_rewrite_batchN_expert.py
python3 tools/build_article_pages.py
python3 tools/audit_guide_prose_quality.py --strict
```
