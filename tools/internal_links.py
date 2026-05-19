#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""サイト内SEO用の内部リンク・用語↔過去問の索引。"""

from __future__ import annotations

import csv
import hashlib
import html
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GLOSSARY_CSV = ROOT / "data" / "glossary_terms.csv"
GUIDE_CSV = ROOT / "data" / "guide_articles.csv"
PAST_CSV = ROOT / "data" / "past_questions.csv"

# 過去問 category → 演習アプリの field（csv_to_chintaikan_eisei_master と揃える）
PAST_CATEGORY_TO_FIELD: dict[str, str] = {
    "賃貸住宅管理業法": "law",
    "維持保全": "law",
    "関連法令": "law",
    "賃貸不動産経営": "law",
    "政策課題・社会情勢": "law",
    "賃貸借契約": "rights",
    "賃貸借": "rights",
    "管理受託契約": "rights",
    "金銭管理": "rights",
    "賃貸借契約実務": "rights",
    "民法・借地借家法": "rights",
    "賃料管理・督促": "rights",
    "原状回復": "rights",
    "サブリース": "rights",
    "管理実務": "rights",
    "建物・設備": "limit",
    "会計・税金・保険": "limit",
    "会計税務": "limit",
}

# 用語 CSV category → field（build_glossary_pages.GLOSSARY_CAT_TO_FIELD と揃える）
GLOSSARY_CAT_TO_FIELD: dict[str, str] = {
    "賃貸住宅管理業法": "law",
    "関連法令": "law",
    "借地借家法": "rights",
    "賃貸借契約": "rights",
    "民法": "rights",
    "原状回復": "rights",
    "管理実務": "rights",
    "建物・設備": "limit",
    "会計・税務・保険": "limit",
    "賃貸経営・PM/AM": "limit",
}

FIELD_LABELS = {"law": "賃管法令・制度", "rights": "契約・実務", "limit": "設備・税務・その他"}

# 過去問 category / 用語 category → 科目別ハブ記事 slug
CATEGORY_GUIDE: dict[str, str] = {
    "賃貸住宅管理業法": "law-subject",
    "関連法令": "law-subject",
    "維持保全": "law-subject",
    "賃貸不動産経営": "law-subject",
    "借地借家法": "rights-subject",
    "賃貸借契約": "rights-subject",
    "民法": "rights-subject",
    "原状回復": "rights-subject",
    "管理実務": "rights-subject",
    "建物・設備": "limit-subject",
    "会計・税務・保険": "limit-subject",
    "賃貸経営・PM/AM": "limit-subject",
}

GENRE_GUIDE: dict[str, str] = {
    "試験概要": "exam-overview",
    "試験対策": "study-plan",
    "過去問活用": "past-questions-how-to-use",
    "学習法": "glossary-how-to-use",
    "科目別対策": "law-subject",
    "法令対策": "law-subject",
    "重要論点": "genjo-kaifuku-guide",
}

FIELD_GUIDE: dict[str, str] = {
    "law": "law-subject",
    "rights": "rights-subject",
    "limit": "limit-subject",
}

LABELS = [("ア", "statement_a"), ("イ", "statement_b"), ("ウ", "statement_c"), ("エ", "statement_d")]


def norm(value: str | None) -> str:
    return (value or "").strip()


def term_slug(term: str, reading: str, used: dict[str, str]) -> str:
    base = f"{term.strip()}|{reading.strip()}"
    h = hashlib.sha256(base.encode("utf-8")).hexdigest()[:16]
    s = f"g-{h}"
    if s not in used:
        used[s] = base
        return s
    n = 2
    while True:
        cand = f"g-{h}-{n}"
        if cand not in used:
            used[cand] = base
            return cand
        n += 1


def term_alias_variants(term: str) -> set[str]:
    variants = {term}
    no_paren = re.sub(r"（[^）]+）|\([^)]*\)", "", term).strip()
    if no_paren and no_paren != term:
        variants.add(no_paren)
    for part in re.findall(r"（([^）]+)）|\(([^)]*)\)", term):
        inner = next((x for x in part if x), "").strip()
        if inner:
            variants.add(inner)
    return {v for v in variants if len(v) >= 2}


def past_question_plain_text(row: dict) -> str:
    parts: list[str] = []
    for key in ("stem", "preamble", "explanation", "category", "tags"):
        t = norm(row.get(key))
        if t:
            parts.append(t)
    for _, key in LABELS:
        t = norm(row.get(key))
        if t:
            parts.append(t)
    for i in range(1, 5):
        t = norm(row.get(f"choice_{i}"))
        if t:
            parts.append(t)
    return " ".join(parts)


def past_field(category: str) -> str | None:
    return PAST_CATEGORY_TO_FIELD.get(category) or GLOSSARY_CAT_TO_FIELD.get(category)


def glossary_field(category: str) -> str | None:
    return GLOSSARY_CAT_TO_FIELD.get(category)


def build_glossary_index() -> tuple[dict[str, str], dict[str, list[str]]]:
    if not GLOSSARY_CSV.is_file():
        return {}, {}
    rows = list(csv.DictReader(GLOSSARY_CSV.read_text(encoding="utf-8-sig").splitlines()))
    used: dict[str, str] = {}
    term_to_href: dict[str, str] = {}
    by_category: dict[str, list[str]] = {}
    for row in rows:
        term = norm(row.get("term"))
        if not term:
            continue
        reading = norm(row.get("reading"))
        slug = term_slug(term, reading, used) + ".html"
        term_to_href[term] = f"terms/{slug}"
        cat = norm(row.get("category"))
        if cat:
            by_category.setdefault(cat, []).append(term)
    return term_to_href, by_category


def guide_titles() -> dict[str, str]:
    if not GUIDE_CSV.is_file():
        return {}
    return {
        norm(r["slug"]): norm(r["title"])
        for r in csv.DictReader(GUIDE_CSV.read_text(encoding="utf-8-sig").splitlines())
        if norm(r.get("slug"))
    }


def guide_slug_for_category(category: str) -> str | None:
    return CATEGORY_GUIDE.get(category) or FIELD_GUIDE.get(glossary_field(category) or "")


def guide_slug_for_genre(genre: str) -> str | None:
    return GENRE_GUIDE.get(genre)


def guide_link(slug: str | None, titles: dict[str, str]) -> tuple[str, str] | None:
    if not slug or slug not in titles:
        return None
    return (titles[slug], f"articles/{slug}/index.html")


def rel_href(from_file: Path, to_rel: str) -> str:
    try:
        return Path(os.path.relpath(Path(to_rel), from_file.parent)).as_posix()
    except ValueError:
        return to_rel


def find_terms_in_text(text: str, term_to_href: dict[str, str], limit: int = 5) -> list[tuple[str, str]]:
    if not text:
        return []
    hits: list[tuple[str, str]] = []
    seen: set[str] = set()
    for term in sorted(term_to_href.keys(), key=len, reverse=True):
        if len(term) < 2:
            continue
        if term in text and term not in seen:
            hits.append((term, term_to_href[term]))
            seen.add(term)
        if len(hits) >= limit:
            break
    return hits


def load_past_pages() -> list[dict]:
    if not PAST_CSV.is_file():
        return []
    pages: list[dict] = []
    for row in csv.DictReader(PAST_CSV.read_text(encoding="utf-8-sig").splitlines()):
        year_s = norm(row.get("exam_year"))
        qno_s = norm(row.get("question_no"))
        if not year_s or not qno_s:
            continue
        year = int(year_s)
        qno = int(qno_s)
        cat = norm(row.get("category"))
        pages.append(
            {
                "year": year,
                "qno": qno,
                "wareki": norm(row.get("exam_wareki")),
                "category": cat,
                "field": past_field(cat),
                "text": past_question_plain_text(row),
                "rel_path": f"q/past/y{year}/q{qno:02d}/index.html",
            }
        )
    return pages


def build_term_past_index(
    entries: list[dict],
    pages: list[dict] | None = None,
    *,
    max_per_term: int = 6,
) -> dict[str, list[dict]]:
    """用語名 → 本文に出現した過去問ページ情報のリスト（新しい年度優先）。"""
    if pages is None:
        pages = load_past_pages()
    if not pages:
        return {}

    term_variants: dict[str, set[str]] = {}
    term_field: dict[str, str | None] = {}
    for e in entries:
        term = norm(e.get("term"))
        if not term:
            continue
        term_variants[term] = term_alias_variants(term)
        term_field[term] = glossary_field(norm(e.get("category")))

    index: dict[str, list[dict]] = {t: [] for t in term_variants}
    seen: dict[str, set[tuple[int, int]]] = {t: set() for t in term_variants}

    for page in pages:
        text = page["text"]
        y, q = page["year"], page["qno"]
        for term, variants in term_variants.items():
            if (y, q) in seen[term]:
                continue
            if any(v in text for v in variants):
                index[term].append(page)
                seen[term].add((y, q))

    for term in index:
        index[term].sort(key=lambda p: (-p["year"], p["qno"]))
        if len(index[term]) > max_per_term:
            index[term] = index[term][:max_per_term]

    # 本文マッチが無い用語は同分野の過去問をフォールバック
    by_field: dict[str, list[dict]] = {}
    for page in pages:
        fid = page.get("field")
        if fid:
            by_field.setdefault(fid, []).append(page)
    for fid in by_field:
        by_field[fid].sort(key=lambda p: (-p["year"], p["qno"]))

    for term, fid in term_field.items():
        if index[term] or not fid:
            continue
        fallback = by_field.get(fid, [])
        index[term] = fallback[:max_per_term]

    return index


def related_past_questions_html(
    term: str,
    category: str,
    rel_path: Path,
    past_hits: list[dict],
    *,
    limit: int = 6,
) -> str:
    """用語詳細ページ用「関連過去問」ブロック。"""
    links: list[tuple[str, str]] = []
    for p in past_hits[:limit]:
        label = f"{p['wareki']} 第{p['qno']}問（{p['category']}）"
        links.append((label, rel_href(rel_path, p["rel_path"])))

    if not links:
        fid = glossary_field(category)
        field_label = FIELD_LABELS.get(fid or "", "関連分野")
        links.append((f"{field_label}の過去問一覧を見る", rel_href(rel_path, "q/index.html")))

    items = "".join(
        f'<li><a href="{html.escape(href)}">{html.escape(label)}</a></li>' for label, href in links
    )
    note = (
        f"「{html.escape(term)}」が問題文・解説に含まれる過去問形式の演習です。"
        "制度改正の影響がある場合は公式情報もあわせて確認してください。"
    )
    return (
        '<section class="q-block term-block term-past-questions" aria-labelledby="term-past-q-h">'
        '<h2 id="term-past-q-h" class="q-h2">関連過去問</h2>'
        f'<p class="term-past-q-note">{note}</p>'
        f'<ul class="term-past-q-list">{items}</ul>'
        f'<p class="term-past-q-more"><a href="{html.escape(rel_href(rel_path, "q/index.html"))}">'
        "過去問一覧へ</a></p>"
        "</section>"
    )


def related_box_html(title: str, links: list[tuple[str, str]]) -> str:
    if not links:
        return ""
    items = "".join(
        f'<a class="related-link" href="{html.escape(href)}">{html.escape(label)}</a>'
        for label, href in links
    )
    return (
        f'<section class="seo-article-section" aria-label="{html.escape(title)}">'
        f'<div class="related-box"><div class="related-box-title">{html.escape(title)}</div>'
        f'<div class="related-links">{items}</div></div></section>'
    )


def exam_name_short() -> str:
    return "賃管"


def article_link_sections(article: dict[str, str], rel_path: Path) -> str:
    term_to_href, by_category = build_glossary_index()
    titles = guide_titles()
    genre = norm(article.get("genre"))
    text = " ".join(norm(article.get(k, "")) for k in ("title", "lead", "meta_description"))
    term_links = find_terms_in_text(text, term_to_href, 5)
    if not term_links:
        for cat in by_category:
            if cat[:2] in text:
                term_links = [(t, term_to_href[t]) for t in by_category[cat][:5] if t in term_to_href]
                break
    term_links = [(label, rel_href(rel_path, href)) for label, href in term_links]

    current_slug = norm(article.get("slug"))
    guide_slug = guide_slug_for_genre(genre)
    guide_links: list[tuple[str, str]] = []
    g = guide_link(guide_slug, titles)
    if g and guide_slug != current_slug:
        guide_links.append((g[0], rel_href(rel_path, g[1])))

    q_links = [(f"過去問一覧（{exam_name_short()}）", rel_href(rel_path, "q/index.html"))]
    parts = [
        related_box_html("関連用語", term_links),
        related_box_html("過去問で確認する", q_links),
    ]
    if guide_links:
        parts.append(related_box_html("あわせて読むガイド", guide_links))
    return "".join(parts)
