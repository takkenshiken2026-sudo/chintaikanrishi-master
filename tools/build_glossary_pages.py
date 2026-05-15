#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data/glossary_terms.csv から用語ページ terms/g-*.html と terms/index.html を生成し、
過去問と合わせた sitemap.xml を書き直す。
"""

from __future__ import annotations

import csv
import hashlib
import html
import json
import re
import sys
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.html_footer import static_footer_block, static_site_header

GLOSSARY_CSV = ROOT / "data" / "glossary_terms.csv"
TERMS_DIR = ROOT / "terms"
BASE_DEFAULT = "https://chintaikanrishi-master.jp"

# index.html の FIELDS（用語カテゴリ →演習アプリの分野チップと揃える）
FIELD_LABELS = {"law": "賃管法令・制度", "rights": "契約・実務", "limit": "設備・税務・その他"}
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


def norm(s: str | None) -> str:
    return (s or "").strip()


def term_slug(term: str, reading: str, used: dict[str, str]) -> str:
    """用語+読みで安定したスラッグ。衝突時は連番を付与。"""
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


def public_url(base: str, rel_path: str) -> str:
    return f"{base.rstrip('/')}/{rel_path.lstrip('/')}"


def rel_to_root(rel_file: Path) -> str:
    depth = len(rel_file.parent.parts)
    return "/".join([".."] * depth) + "/index.html"


def rel_css(rel_file: Path) -> str:
    depth = len(rel_file.parent.parts)
    return "/".join([".."] * depth) + "/site-pages.css"


def glossary_field_id(category: str) -> str | None:
    return GLOSSARY_CAT_TO_FIELD.get(norm(category))


def glossary_field_badge_html(category: str) -> str:
    fid = glossary_field_id(category)
    if not fid:
        return ""
    label = FIELD_LABELS.get(fid, fid)
    return f'<span class="term-field-badge term-field-{fid}">{html.escape(label)}</span>'


def meta_description(text: str, limit: int = 155) -> str:
    one = re.sub(r"\s+", " ", text).strip()
    if len(one) <= limit:
        return one
    return one[: limit - 1] + "…"


def split_semicolon(s: str) -> list[str]:
    return [x.strip() for x in (s or "").split(";") if x.strip()]


def write_sitemap(urls: list[str], out: Path) -> None:
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for u in sorted(set(urls)):
        lines.append("  <url>")
        lines.append(f"    <loc>{xml_escape(u)}</loc>")
        lines.append("    <changefreq>monthly</changefreq>")
        lines.append("  </url>")
    lines.append("</urlset>")
    out.write_text("\n".join(lines) + "\n", encoding="utf-8")


def collect_sitemap_urls(base: str) -> list[str]:
    urls = [
        f"{base}/",
        f"{base}/index.html",
        f"{base}/about.html",
        f"{base}/privacy.html",
        f"{base}/related-sites.html",
        f"{base}/articles/index.html",
        f"{base}/q/index.html",
    ]
    qroot = ROOT / "q"
    if qroot.is_dir():
        for p in sorted(qroot.rglob("index.html")):
            rel = p.relative_to(ROOT).as_posix()
            urls.append(f"{base}/{rel}")
    if (TERMS_DIR / "index.html").is_file():
        urls.append(f"{base}/terms/index.html")
    for p in sorted(TERMS_DIR.glob("g-*.html")):
        rel = p.relative_to(ROOT).as_posix()
        urls.append(f"{base}/{rel}")
    return urls


def build_term_html(entry: dict, rel_path: Path, base_url: str) -> str:
    term = entry["term"]
    reading = entry["reading"]
    category = entry["category"]
    tags = entry["tags"]
    short_def = entry["short_def"]
    definition = entry["definition"]
    related = entry["related_terms"]
    legal = entry["legal_basis"]
    importance = entry["importance"]
    explanation = entry["explanation"]
    slug_file = entry["slug_file"]

    title = f"{term}（{reading}）｜用語解説｜賃管マスター"
    desc = meta_description(short_def or definition or term)
    canonical = public_url(base_url, f"terms/{slug_file}")
    root_idx = rel_to_root(rel_path)
    css_href = rel_css(rel_path)

    imp_html = ""
    if importance:
        imp_html = f'<p class="term-imp"><span class="term-imp-label">重要度</span> {html.escape(importance)}</p>'

    tags_list = split_semicolon(tags)
    tags_html = ""
    if tags_list:
        tags_html = (
            "<ul class=\"term-tags\">"
            + "".join(f"<li>{html.escape(t)}</li>" for t in tags_list)
            + "</ul>"
        )

    rel_list = split_semicolon(related)
    rel_html = ""
    if rel_list:
        rel_html = (
            '<h2 id="term-related-h" class="q-h2">関連用語</h2><ul class="term-related">'
            + "".join(f"<li>{html.escape(x)}</li>" for x in rel_list)
            + "</ul>"
        )

    def block(sec_id: str, label: str, body: str) -> str:
        if not body.strip():
            return ""
        hid = f"term-sec-{sec_id}"
        b = html.escape(body).replace("\n", "<br>\n")
        return (
            f'<section class="q-block term-block" aria-labelledby="{hid}">'
            f'<h2 id="{hid}" class="q-h2">{html.escape(label)}</h2>'
            f'<div class="q-stem">{b}</div></section>'
        )

    tags_wrap = ""
    if tags_html:
        tags_wrap = '<div class="term-tags-wrap"><span class="term-tags-label">タグ</span>' + tags_html + "</div>"

    rel_section = ""
    if rel_html:
        rel_section = f'<section class="q-block term-block" aria-labelledby="term-related-h">{rel_html}</section>'

    badge_html = glossary_field_badge_html(category)
    meta_bits: list[str] = ['<span class="q-id">用語</span>']
    if badge_html:
        meta_bits.append(badge_html)
    if category:
        meta_bits.append(f"<span>{html.escape(category)}</span>")
    meta_line = " · ".join(meta_bits)

    site_header = static_site_header(
        root_href=root_idx,
        breadcrumb_items=[
            ("トップ", root_idx),
            ("用語解説", "index.html"),
            (term, None),
        ],
    )

    app_glossary_href = f"{root_idx}#glossary"

    json_ld = {
        "@context": "https://schema.org",
        "@graph": [
            {
                "@type": "DefinedTerm",
                "@id": canonical + "#term",
                "name": term,
                "description": meta_description(definition or short_def, 300),
                "inDefinedTermSet": public_url(base_url, "terms/index.html"),
            },
            {
                "@type": "WebPage",
                "@id": canonical + "#webpage",
                "url": canonical,
                "name": title,
                "description": desc,
                "inLanguage": "ja-JP",
            },
            {
                "@type": "BreadcrumbList",
                "itemListElement": [
                    {"@type": "ListItem", "position": 1, "name": "トップ", "item": public_url(base_url, "index.html")},
                    {"@type": "ListItem", "position": 2, "name": "用語解説", "item": public_url(base_url, "terms/index.html")},
                    {"@type": "ListItem", "position": 3, "name": term, "item": canonical},
                ],
            },
        ],
    }

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<link rel="canonical" href="{html.escape(canonical)}">
<meta property="og:type" content="article">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="{html.escape(desc)}">
<meta property="og:url" content="{html.escape(canonical)}">
<meta name="twitter:card" content="summary">
<link rel="stylesheet" href="{html.escape(css_href)}">
<script type="application/ld+json">
{json.dumps(json_ld, ensure_ascii=False, indent=2)}
</script>
</head>
<body class="q-static-body">
{site_header}
<main class="q-static-main">
  <p class="q-meta">{meta_line}</p>
  {imp_html}
  <h1 class="q-h1">{html.escape(term)}<span class="term-reading">（{html.escape(reading)}）</span></h1>
  {tags_wrap}
  {block("short", "ひとこと", short_def)}
  {block("def", "定義", definition)}
  {block("legal", "法令・根拠", legal)}
  {block("exam", "試験で押さえる", explanation)}
  {rel_section}
  <p class="q-app-link"><a href="{html.escape(app_glossary_href)}">アプリで用語解説を開く</a></p>
</main>
{static_footer_block(rel_path)}
</body>
</html>
"""


def build_terms_index(entries: list[dict], base_url: str) -> str:
    by_cat: dict[str, list[dict]] = {}
    for e in entries:
        by_cat.setdefault(e["category"] or "その他", []).append(e)
    for c in by_cat:
        by_cat[c].sort(key=lambda x: x["term"])

    blocks = []
    for cat in sorted(by_cat.keys()):
        lis = []
        for e in by_cat[cat]:
            href = e["slug_file"]
            fb = glossary_field_badge_html(e["category"])
            lead = f'<span class="term-list-field">{fb}</span>' if fb else ""
            lis.append(
                f"<li>{lead}<a href=\"{html.escape(href)}\">{html.escape(e['term'])}</a></li>"
            )
        blocks.append(
            f'<section class="glos-cat-section term-cat-section"><h2 class="glos-cat-heading">{html.escape(cat)}</h2>'
            f'<ul class="term-cat-list term-cat-list--fields">{"".join(lis)}</ul></section>'
        )

    terms_header = static_site_header(
        root_href="../index.html",
        breadcrumb_items=[("トップ", "../index.html"), ("用語解説", None)],
    )

    canonical = public_url(base_url, "terms/index.html")
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>用語解説｜賃管マスター（賃貸不動産経営管理士）</title>
<meta name="description" content="賃貸不動産経営管理士試験向けの用語集。分野別に用語を一覧できます。">
<link rel="canonical" href="{html.escape(canonical)}">
<link rel="stylesheet" href="../site-pages.css">
</head>
<body class="q-static-body">
{terms_header}
<main class="q-static-main">
  <h1 class="q-h1">用語解説</h1>
  <p class="q-meta">全 {len(entries)} 語</p>
  <p class="glos-static-intro term-index-intro">演習アプリ内の<strong><a href="../index.html#glossary">用語解説</a></strong>と同じ分野ラベル（賃管法令・制度／契約・実務／設備・税務・その他）で整理しています。検索や折りたたみカードはアプリ側で利用できます。</p>
  {"".join(blocks)}
</main>
{static_footer_block(Path("terms/index.html"))}
</body>
</html>
"""


def load_glossary_rows() -> list[dict]:
    if not GLOSSARY_CSV.is_file():
        raise FileNotFoundError(str(GLOSSARY_CSV))
    text = GLOSSARY_CSV.read_text(encoding="utf-8-sig")
    return list(csv.DictReader(text.splitlines()))


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=BASE_DEFAULT)
    args = ap.parse_args()
    base = args.base_url.rstrip("/")

    rows = load_glossary_rows()
    used_slugs: dict[str, str] = {}
    entries: list[dict] = []
    for i, row in enumerate(rows, start=2):
        term = norm(row.get("term"))
        if not term:
            raise ValueError(f"line {i}: term が空です")
        reading = norm(row.get("reading"))
        slug_file = term_slug(term, reading, used_slugs) + ".html"
        entries.append(
            {
                "term": term,
                "reading": reading,
                "category": norm(row.get("category")),
                "tags": norm(row.get("tags")),
                "short_def": norm(row.get("short_def")),
                "definition": norm(row.get("definition")),
                "related_terms": norm(row.get("related_terms")),
                "legal_basis": norm(row.get("legal_basis")),
                "importance": norm(row.get("importance")),
                "explanation": norm(row.get("explanation")),
                "slug_file": slug_file,
            }
        )

    TERMS_DIR.mkdir(parents=True, exist_ok=True)
    for stale in TERMS_DIR.glob("g-*.html"):
        stale.unlink()

    for e in entries:
        out_file = TERMS_DIR / e["slug_file"]
        rel_path = out_file.relative_to(ROOT)
        out_file.write_text(build_term_html(e, rel_path, base), encoding="utf-8")

    (TERMS_DIR / "index.html").write_text(build_terms_index(entries, base), encoding="utf-8")

    urls = collect_sitemap_urls(base)
    write_sitemap(urls, ROOT / "sitemap.xml")

    print(f"Wrote {len(entries)} term pages under {TERMS_DIR}")
    print(f"Wrote {TERMS_DIR / 'index.html'}")
    print(f"Updated {ROOT / 'sitemap.xml'} ({len(set(urls))} URLs)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except FileNotFoundError as e:
        print(e, file=sys.stderr)
        raise SystemExit(1)
