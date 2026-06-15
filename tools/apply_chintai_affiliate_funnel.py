#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""学習系ガイドへ公開済み affiliate 比較記事の導線を追加する（賃管）。"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "guide_articles.csv"

AFFILIATE_TITLES = {
    "affiliate-textbooks-recommend": "賃貸不動産経営管理士のおすすめテキスト3選【2026年度版・独学】",
    "affiliate-problem-books": "賃貸不動産経営管理士のおすすめ問題集3選【一問一答・過去問2026】",
    "affiliate-mock-exam-materials": "賃貸不動産経営管理士の直前対策3選【予想模試・チェックシート2026】",
    "affiliate-free-vs-paid-study": "賃貸不動産経営管理士試験の無料と有料教材の使い分け【独学2026】",
    "affiliate-beginner-material-set": "賃貸不動産経営管理士試験の初学者向け教材セット3選【2026年度版·テキスト+問題集】",
    "affiliate-qualification-support-service": (
        "賃貸不動産経営管理士試験の受験支援サービス比較"
        "【公式申込 vs 書類チェック vs 講座付帯】【2026年度版】"
    ),
}

BODY = {
    "affiliate-textbooks-recommend": (
        "テキスト1冊は、[おすすめテキスト3選](../affiliate-textbooks-recommend/) "
        "で3出版社を比較してから固定すると、途中で乗り換えずに済みます。"
    ),
    "affiliate-problem-books": (
        "演習1冊は、[おすすめ問題集3選](../affiliate-problem-books/) "
        "で収録形式と解説量を比較してから週次計画に組み込むと迷いが減ります。"
    ),
    "affiliate-mock-exam-materials": (
        "直前の模試・短問は、[おすすめ直前対策3選](../affiliate-mock-exam-materials/) "
        "で用途の違いを確認してから9月以降のカレンダーに入れると安全です。"
    ),
    "affiliate-beginner-material-set": (
        "初めて揃える2冊セットは、[初学者向け教材セット3選](../affiliate-beginner-material-set/) "
        "で予算と章立てのつながりを比較してから7月購入に進むと無駄が減ります。"
    ),
}

GUIDE_AFFILIATE: dict[str, tuple[str, int]] = {
    "exam-overview": ("affiliate-textbooks-recommend", 2),
    "textbook-selection": ("affiliate-textbooks-recommend", 2),
    "problem-book-selection": ("affiliate-problem-books", 2),
    "study-plan": ("affiliate-beginner-material-set", 2),
    "past-questions-how-to-use": ("affiliate-problem-books", 2),
    "past-questions-by-field": ("affiliate-problem-books", 2),
    "timed-practice": ("affiliate-problem-books", 2),
    "ichimon-practice-mode": ("affiliate-mock-exam-materials", 2),
    "pass-score": ("affiliate-problem-books", 2),
    "final-day-checklist": ("affiliate-mock-exam-materials", 2),
    "retake-strategy": ("affiliate-problem-books", 2),
    "retake-review-plan": ("affiliate-problem-books", 2),
    "official-info-sources": ("affiliate-beginner-material-set", 2),
    "exam-day-items": ("affiliate-mock-exam-materials", 2),
    "exam-day-flow": ("affiliate-mock-exam-materials", 2),
    "exempt-invalid-questions": ("affiliate-problem-books", 2),
}

SECONDARY_AFFILIATE: dict[str, str] = {
    "exam-overview": "affiliate-beginner-material-set",
    "textbook-selection": "affiliate-problem-books",
    "problem-book-selection": "affiliate-textbooks-recommend",
    "past-questions-how-to-use": "affiliate-textbooks-recommend",
    "timed-practice": "affiliate-mock-exam-materials",
    "pass-score": "affiliate-mock-exam-materials",
    "retake-strategy": "affiliate-mock-exam-materials",
    "official-info-sources": "affiliate-textbooks-recommend",
    "exam-day-flow": "affiliate-problem-books",
}

EXCLUDE_SLUGS = frozenset()


def _split_related(value: str) -> list[str]:
    return [x.strip() for x in (value or "").split(";") if x.strip()]


def _append_related(value: str, token: str) -> str:
    parts = _split_related(value)
    slug = token.split(":", 1)[0]
    if any(p.split(":", 1)[0] == slug for p in parts):
        return ";".join(parts)
    parts.append(token)
    return ";".join(parts)


def _append_body(body: str, aff_slug: str) -> str:
    sentence = BODY[aff_slug]
    if aff_slug in (body or "") or sentence in (body or ""):
        return body
    text = (body or "").rstrip()
    if not text:
        return sentence
    if not text.endswith("。"):
        text += "。"
    return text + sentence


def apply_guide_updates(rows: list[dict[str, str]]) -> int:
    by_slug = {r["slug"]: r for r in rows}
    changed = 0
    for slug, (aff_slug, sec_n) in GUIDE_AFFILIATE.items():
        if slug in EXCLUDE_SLUGS:
            continue
        row = by_slug.get(slug)
        if not row or (row.get("content_status") or "").strip() != "published":
            continue
        body_key = f"section_{sec_n}_body"
        old_body = row.get(body_key, "")
        new_body = _append_body(old_body, aff_slug)
        if new_body != old_body:
            row[body_key] = new_body

        token = f"{aff_slug}:{AFFILIATE_TITLES[aff_slug]}"
        new_rl = _append_related(row.get("related_links", ""), token)
        sec = SECONDARY_AFFILIATE.get(slug)
        if sec:
            new_rl = _append_related(new_rl, f"{sec}:{AFFILIATE_TITLES[sec]}")
        if new_rl != row.get("related_links", "") or new_body != old_body:
            row["related_links"] = new_rl
            changed += 1
    return changed


def main() -> None:
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    if not fieldnames:
        raise SystemExit("guide_articles.csv: no header")

    changed = apply_guide_updates(rows)

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)

    print(f"Guide funnel: {len(GUIDE_AFFILIATE)} targets, {changed} row(s) updated")


if __name__ == "__main__":
    main()
