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

from tools.html_footer import (
    site_page_footer,
    site_page_header,
    site_page_wrap_close,
    site_page_wrap_open,
)

HEAD_FONTS = """<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Noto+Sans+JP:wght@400;500;600;700&display=swap" rel="stylesheet">"""

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

# 用語索引ページの科目チップ・見出しの並び（CSV のカテゴリ名と一致）
GLOSSARY_CAT_ORDER = (
    "賃貸住宅管理業法",
    "関連法令",
    "借地借家法",
    "賃貸借契約",
    "民法",
    "原状回復",
    "管理実務",
    "建物・設備",
    "会計・税務・保険",
    "賃貸経営・PM/AM",
    "その他",
)


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


def ordered_term_categories(by_cat: dict[str, list]) -> list[str]:
    keys = set(by_cat.keys())
    out: list[str] = [c for c in GLOSSARY_CAT_ORDER if c in keys]
    for c in sorted(keys):
        if c not in out:
            out.append(c)
    return out


def meta_description(text: str, limit: int = 155) -> str:
    one = re.sub(r"\s+", " ", text).strip()
    if len(one) <= limit:
        return one
    return one[: limit - 1] + "…"


def split_semicolon(s: str) -> list[str]:
    return [x.strip() for x in (s or "").split(";") if x.strip()]


def split_sentences(s: str) -> list[str]:
    text = re.sub(r"\s+", " ", s or "").strip()
    if not text:
        return []
    return [p.strip() for p in re.findall(r"[^。！？]+[。！？]?", text) if p.strip()]


def study_points(explanation: str, limit: int = 4) -> list[str]:
    points: list[str] = []
    for sentence in split_sentences(explanation):
        s = sentence.rstrip("。")
        if len(s) < 14:
            continue
        if s.endswith("です") and "とは、" in s:
            continue
        points.append(s + "。")
        if len(points) >= limit:
            break
    return points


def make_term_lookup(entries: list[dict]) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for e in entries:
        term = e["term"]
        lookup[term] = e["slug_file"]
        lookup[re.sub(r"\s+", "", term)] = e["slug_file"]
    return lookup


def related_terms_html(related: str, term_lookup: dict[str, str]) -> str:
    items: list[str] = []
    for label in split_semicolon(related):
        href = term_lookup.get(label) or term_lookup.get(re.sub(r"\s+", "", label))
        if href:
            items.append(f'<li><a href="{html.escape(href)}">{html.escape(label)}</a></li>')
        else:
            items.append(f"<li>{html.escape(label)}</li>")
    if not items:
        return ""
    return '<h2 id="term-related-h" class="q-h2">関連用語</h2><ul class="term-related">' + "".join(items) + "</ul>"


def legal_basis_html(legal: str) -> str:
    items = split_semicolon(legal)
    if len(items) <= 1:
        return html.escape(legal).replace("\n", "<br>\n")
    return '<ul class="term-legal-list">' + "".join(f"<li>{html.escape(x)}</li>" for x in items) + "</ul>"


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


def build_term_html(entry: dict, rel_path: Path, base_url: str, term_lookup: dict[str, str]) -> str:
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

    title = f"{term}とは？意味・根拠・試験ポイント｜賃管マスター"
    desc = meta_description(
        f"{term}（{reading}）の意味、法令・根拠、試験で押さえるポイントを賃貸不動産経営管理士向けに整理。{short_def or definition}"
    )
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

    rel_html = related_terms_html(related, term_lookup)

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

    def raw_block(sec_id: str, label: str, body_html: str) -> str:
        if not body_html.strip():
            return ""
        hid = f"term-sec-{sec_id}"
        return (
            f'<section class="q-block term-block" aria-labelledby="{hid}">'
            f'<h2 id="{hid}" class="q-h2">{html.escape(label)}</h2>'
            f'<div class="q-stem">{body_html}</div></section>'
        )

    tags_wrap = ""
    if tags_html:
        tags_wrap = '<div class="term-tags-wrap"><span class="term-tags-label">タグ</span>' + tags_html + "</div>"

    rel_section = ""
    if rel_html:
        rel_section = f'<section class="q-block term-block" aria-labelledby="term-related-h">{rel_html}</section>'

    lead = (
        f"{term}は、{short_def.rstrip('。')}。"
        f"賃貸不動産経営管理士試験では、{category}分野の用語として、意味・根拠・似た用語との違いをセットで押さえると理解しやすくなります。"
    )
    points = study_points(explanation)
    points_html = ""
    if points:
        points_html = '<ol class="term-point-list">' + "".join(f"<li>{html.escape(p)}</li>" for p in points) + "</ol>"

    badge_html = glossary_field_badge_html(category)
    meta_bits: list[str] = ['<span class="q-id">用語</span>']
    if badge_html:
        meta_bits.append(badge_html)
    if category:
        meta_bits.append(f"<span>{html.escape(category)}</span>")
    meta_line = " · ".join(meta_bits)

    crumb_items = [
        ("トップ", "index.html"),
        ("用語解説一覧", "terms/index.html"),
        (term, None),
    ]
    page_header = site_page_header(rel_path, current="terms", breadcrumb_items=crumb_items)
    page_footer = site_page_footer(rel_path, current="terms")

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
                "@type": "Article",
                "@id": canonical + "#article",
                "headline": title,
                "description": desc,
                "about": term,
                "mainEntityOfPage": canonical,
                "inLanguage": "ja-JP",
                "isPartOf": public_url(base_url, "terms/index.html"),
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
{HEAD_FONTS}
<link rel="stylesheet" href="{html.escape(css_href)}">
<script type="application/ld+json">
{json.dumps(json_ld, ensure_ascii=False, indent=2)}
</script>
</head>
<body>
{site_page_wrap_open()}
{page_header}
<main class="site-page-main term-page-main">
  <p class="q-meta">{meta_line}</p>
  {imp_html}
  <h1 class="q-h1">{html.escape(term)}<span class="term-reading">（{html.escape(reading)}）</span></h1>
  <p class="term-lead">{html.escape(lead)}</p>
  {tags_wrap}
  {block("short", "ひとこと", short_def)}
  {raw_block("points", "試験で押さえるポイント", points_html)}
  {block("def", "定義", definition)}
  {raw_block("legal", "法令・根拠", legal_basis_html(legal))}
  {block("exam", "試験で押さえる", explanation)}
  {rel_section}
  <p class="q-app-link"><a href="{html.escape(app_glossary_href)}">アプリで用語解説を開く</a></p>
</main>
{page_footer}
{site_page_wrap_close()}
</body>
</html>
"""


def build_terms_index(entries: list[dict], base_url: str) -> str:
    by_cat: dict[str, list[dict]] = {}
    for e in entries:
        by_cat.setdefault(e["category"] or "その他", []).append(e)
    for c in by_cat:
        by_cat[c].sort(key=lambda x: x["term"])

    cat_keys = ordered_term_categories(by_cat)
    body_sections: list[str] = []
    for i, cat in enumerate(cat_keys):
        lis = []
        for e in by_cat[cat]:
            href = e["slug_file"]
            lis.append(
                f'    <li><a href="{html.escape(href)}">{html.escape(e["term"])}</a></li>'
            )
        hid = f"terms-idx-cat-{i}"
        body_sections.append(
            f'<section class="terms-idx-cat" aria-labelledby="{hid}">\n'
            f'  <h2 id="{hid}">{html.escape(cat)}</h2>\n'
            f'  <ul class="terms-idx-list">\n'
            + "\n".join(lis)
            + "\n  </ul>\n</section>"
        )
    body_html = "\n".join(body_sections)

    chip_lines = [
        '    <button type="button" class="terms-idx-chip on" data-cat="all">すべて</button>'
    ]
    for cat in cat_keys:
        chip_lines.append(
            "    "
            f'<button type="button" class="terms-idx-chip" data-cat="{html.escape(cat, quote=True)}">'
            f"{html.escape(cat)}</button>"
        )
    chips_html = "\n".join(chip_lines)

    list_items_ld: list[dict] = []
    pos = 1
    for cat in cat_keys:
        for e in by_cat[cat]:
            list_items_ld.append(
                {
                    "@type": "ListItem",
                    "position": pos,
                    "name": e["term"],
                    "item": public_url(base_url, f"terms/{e['slug_file']}"),
                }
            )
            pos += 1
    ld = {
        "@context": "https://schema.org",
        "@type": "ItemList",
        "name": "賃貸不動産経営管理士試験 用語解説一覧",
        "description": "試験で出やすい用語ごとの解説記事への索引です。",
        "numberOfItems": len(entries),
        "itemListElement": list_items_ld,
    }
    ld_json = json.dumps(ld, ensure_ascii=False, indent=2)

    n_terms = len(entries)
    terms_idx_script = f"""<script>
(() => {{
  try {{ if ('scrollRestoration' in history) history.scrollRestoration = 'manual'; }} catch (_e) {{}}
  window.scrollTo(0, 0);
  const q = document.getElementById('terms-idx-q');
  const chips = Array.from(document.querySelectorAll('.terms-idx-chip[data-cat]'));
  const cats = Array.from(document.querySelectorAll('.terms-idx-cat'));
  const totalEl = document.getElementById('terms-idx-total');
  const hitEl = document.getElementById('terms-idx-hit');
  let activeCat = 'all';
  function norm(s) {{
    return (s || '').toString().trim().toLowerCase();
  }}
  function apply() {{
    const query = norm(q.value);
    let shown = 0;
    cats.forEach((sec) => {{
      const cat = sec.querySelector('h2')?.textContent || '';
      const catOk = activeCat === 'all' || cat === activeCat;
      const items = Array.from(sec.querySelectorAll('li'));
      let anyInCat = 0;
      items.forEach((li) => {{
        const a = li.querySelector('a');
        const t = norm(a?.textContent || '');
        const ok = catOk && (!query || t.includes(query));
        li.classList.toggle('hide', !ok);
        if (ok) {{
          anyInCat++;
          shown++;
        }}
      }});
      sec.classList.toggle('hide', anyInCat === 0);
    }});
    if (totalEl) totalEl.textContent = String({n_terms});
    if (hitEl) {{
      hitEl.textContent =
        (query || activeCat !== 'all') ? '表示：' + shown + '件' : '';
    }}
  }}
  q.addEventListener('input', apply);
  chips.forEach((btn) => {{
    btn.addEventListener('click', () => {{
      chips.forEach((b) => b.classList.remove('on'));
      btn.classList.add('on');
      activeCat = btn.dataset.cat || 'all';
      apply();
    }});
  }});
  apply();
}})();
</script>"""

    idx_path = Path("terms/index.html")
    terms_header = site_page_header(
        idx_path,
        current="terms",
        breadcrumb_items=[("トップ", "index.html"), ("用語解説一覧", None)],
        wide=True,
    )
    terms_footer = site_page_footer(idx_path, current="terms", wide=True)

    canonical = public_url(base_url, "terms/index.html")
    title = "用語解説一覧（全記事索引）｜賃管マスター（賃貸不動産経営管理士）"
    desc = (
        "賃貸不動産経営管理士試験の重要用語を一覧し、各用語の解説記事へリンクします。"
        "賃管法令・契約実務・設備税務などの語句を整理しています。"
    )
    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{html.escape(title)}</title>
<meta name="description" content="{html.escape(desc)}">
<meta name="robots" content="index, follow">
<link rel="canonical" href="{html.escape(canonical)}">
<meta property="og:type" content="website">
<meta property="og:url" content="{html.escape(canonical)}">
<meta property="og:title" content="{html.escape(title)}">
<meta property="og:description" content="試験で出やすい用語ごとの解説記事への索引です。">
<meta property="og:locale" content="ja_JP">
<script type="application/ld+json">
{ld_json}
</script>
{HEAD_FONTS}
<link rel="stylesheet" href="../site-pages.css">
</head>
<body>
{site_page_wrap_open()}
{terms_header}
<main class="site-page-main terms-idx-main">
  <h1 class="terms-idx-page-title">用語解説一覧（全記事索引）</h1>
  <p class="terms-idx-lead">賃貸不動産経営管理士試験で頻出の用語を分野別にまとめ、各用語の解説記事（静的HTML）へ直接リンクします。上の検索・分野フィルタで目的の用語に素早く到達できます。演習アプリ内の<strong><a href="../index.html#glossary">用語解説</a></strong>では検索や折りたたみカードも利用できます。</p>

  <div class="terms-idx-meta-row">
    <span class="terms-idx-pill">全 <span id="terms-idx-total">{n_terms}</span> 記事</span>
    <div class="terms-idx-search" role="search" aria-label="用語検索">
      <input id="terms-idx-q" type="search" inputmode="search" placeholder="例：定期借家、原状回復、賃貸住宅管理業法…" autocomplete="off">
    </div>
  </div>

  <div class="terms-idx-chips" aria-label="分野フィルタ">
{chips_html}
  </div>

  <section class="terms-idx-panel" aria-label="用語一覧">
{body_html}
    <div class="terms-idx-panel-footer">
      <span id="terms-idx-hit"></span>
      <div class="terms-idx-panel-footer-app">学習アプリ本体は <a href="../index.html">トップ</a> から利用できます。</div>
    </div>
  </section>
</main>
{terms_footer}
{site_page_wrap_close()}
{terms_idx_script}
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

    term_lookup = make_term_lookup(entries)

    TERMS_DIR.mkdir(parents=True, exist_ok=True)
    for stale in TERMS_DIR.glob("g-*.html"):
        stale.unlink()

    for e in entries:
        out_file = TERMS_DIR / e["slug_file"]
        rel_path = out_file.relative_to(ROOT)
        out_file.write_text(build_term_html(e, rel_path, base, term_lookup), encoding="utf-8")

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
