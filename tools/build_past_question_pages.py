#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
data/past_questions.csv から静的問題ページ q/past/... を生成し、
q/index.html・sitemap.xml・robots.txt を更新する。
"""

from __future__ import annotations

import csv
import html
import json
import re
import shutil
import sys
from pathlib import Path
from xml.sax.saxutils import escape as xml_escape

ROOT = Path(__file__).resolve().parents[1]
import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.html_footer import static_footer_block

DATA_CSV = ROOT / "data" / "past_questions.csv"
Q_ROOT = ROOT / "q"
BASE_DEFAULT = "https://chintaikanrishi-master.jp"

LABELS = [("ア", "statement_a"), ("イ", "statement_b"), ("ウ", "statement_c"), ("エ", "statement_d")]


def norm(s: str | None) -> str:
    return (s or "").strip()


def parse_correct(raw: str) -> int | None:
    raw = norm(raw)
    if not raw:
        return None
    try:
        n = int(raw)
    except ValueError:
        return None
    if 1 <= n <= 4:
        return n
    return None


def build_stem_html(row: dict) -> str:
    parts: list[str] = []
    stem = norm(row.get("stem"))
    preamble = norm(row.get("preamble"))
    br = "<br>\n"
    if stem:
        parts.append(f"<p>{html.escape(stem).replace(chr(10), br)}</p>")
    if preamble:
        parts.append(f"<p>{html.escape(preamble).replace(chr(10), br)}</p>")
    stmts: list[tuple[str, str]] = []
    for lab, key in LABELS:
        t = norm(row.get(key))
        if t:
            stmts.append((lab, t))
    if stmts:
        lis = "".join(
            f"<li><strong>{html.escape(lab)}</strong> {html.escape(t).replace(chr(10), br)}</li>"
            for lab, t in stmts
        )
        parts.append(f'<ol class="q-stmt-list" style="list-style:none;padding-left:0;">{lis}</ol>')
    return "\n".join(parts) if parts else "<p>（問題文なし）</p>"


def meta_description(text: str, limit: int = 155) -> str:
    one = re.sub(r"\s+", " ", text).strip()
    if len(one) <= limit:
        return one
    return one[: limit - 1] + "…"


def rel_to_root(rel_file: Path) -> str:
    depth = len(rel_file.parent.parts)
    return "/".join([".."] * depth) + "/index.html"


def rel_to_q_index(rel_file: Path) -> str:
    """q/past/.../index.html から q/index.html へ"""
    depth = len(rel_file.parent.parts)
    up = max(depth - 1, 1)
    return "/".join([".."] * up) + "/index.html"


def rel_css(rel_file: Path) -> str:
    depth = len(rel_file.parent.parts)
    return "/".join([".."] * depth) + "/site-pages.css"


def public_url(base: str, rel_path: str) -> str:
    return f"{base.rstrip('/')}/{rel_path.lstrip('/')}"


def load_rows() -> list[dict]:
    text = DATA_CSV.read_text(encoding="utf-8-sig")
    return list(csv.DictReader(text.splitlines()))


def page_dict(row: dict, line_no: int) -> dict:
    year = int(row["exam_year"])
    qno = int(row["question_no"])
    opts = [norm(row.get(f"choice_{i}")) for i in range(1, 5)]
    if not all(opts):
        raise ValueError(f"line {line_no}: 選択肢欠け {year}-{qno}")
    inv = norm(row.get("is_invalidated", "")).upper() == "TRUE"
    cor = parse_correct(row.get("correct"))
    if cor is None and not inv:
        raise ValueError(f"line {line_no}: 正答なし {year}-{qno}")
    wareki = norm(row.get("exam_wareki"))
    cat = norm(row.get("category"))
    typ = norm(row.get("type")) or "single"
    stem_plain = norm(row.get("stem"))
    exp = norm(row.get("explanation")) or "（解説は未入力です。）"
    return {
        "year": year,
        "qno": qno,
        "wareki": wareki,
        "category": cat,
        "type": typ,
        "stem_html": build_stem_html(row),
        "stem_plain": stem_plain,
        "opts": opts,
        "correct": cor,
        "is_exempt": norm(row.get("is_exempt", "")).upper() == "TRUE",
        "is_invalidated": inv,
        "note": norm(row.get("note")),
        "exp": exp,
        "id": f"past-{year}-{qno:02d}",
        "rel_path": f"q/past/y{year}/q{qno:02d}/index.html",
    }


def build_question_html(page: dict, rel_path: Path, base_url: str) -> str:
    title_mid = f"{page['wareki']} 第{page['qno']}問・{page['category']}"
    title = f"{title_mid}｜賃管マスター（賃貸不動産経営管理士）"
    desc = meta_description(page["stem_plain"] or page["category"])
    canonical = public_url(base_url, page["rel_path"])
    root_idx = rel_to_root(rel_path)
    css_href = rel_css(rel_path)

    opts_html = "".join(
        f'<li class="q-opt"><span class="q-opt-num">（{i}）</span> {html.escape(o)}</li>'
        for i, o in enumerate(page["opts"], start=1)
    )

    if page["is_invalidated"] or page["correct"] is None:
        ans_block = (
            "<p>本問は試験上「出題無効」となった年度があります（"
            + html.escape(page["note"] or "公式の扱いを確認してください")
            + "）。学習用に選択肢のみ掲載します。</p>"
        )
    else:
        ans_block = f'<p>正答は <strong>（{page["correct"]}）</strong> です。</p>'

    badges = []
    if page["is_exempt"]:
        badges.append('<span class="q-badge">試験免除出題</span>')
    if page["is_invalidated"]:
        badges.append('<span class="q-badge q-badge-warn">出題無効</span>')
    badge_html = ("<p class=\"q-badges\">" + " ".join(badges) + "</p>") if badges else ""

    exp_html = html.escape(page["exp"]).replace("\n", "<br>\n")

    json_ld = {
        "@context": "https://schema.org",
        "@graph": [
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
                    {"@type": "ListItem", "position": 2, "name": "過去問一覧", "item": public_url(base_url, "q/index.html")},
                    {"@type": "ListItem", "position": 3, "name": title_mid, "item": canonical},
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
<header class="q-static-header">
  <p class="q-static-brand"><a href="{html.escape(root_idx)}">賃管マスター</a>（賃貸不動産経営管理士）</p>
  <nav aria-label="パンくず">
    <ol class="q-breadcrumb">
      <li><a href="{html.escape(root_idx)}">トップ</a></li>
      <li><a href="{html.escape(rel_to_q_index(rel_path))}">過去問一覧</a></li>
      <li aria-current="page">{html.escape(title_mid)}</li>
    </ol>
  </nav>
</header>
<main class="q-static-main">
  <p class="q-meta"><span class="q-id">ID: <code>{html.escape(page["id"])}</code></span> · <span>{html.escape(page["category"])}</span> · <span>{html.escape(page["type"])}</span></p>
  {badge_html}
  <h1 class="q-h1">{html.escape(title_mid)}</h1>
  <section class="q-block" aria-labelledby="q-stem-h">
    <h2 id="q-stem-h" class="q-h2">問題</h2>
    <div class="q-stem">{page["stem_html"]}</div>
  </section>
  <section class="q-block" aria-labelledby="q-opts-h">
    <h2 id="q-opts-h" class="q-h2">選択肢</h2>
    <ol class="q-opts">
      {opts_html}
    </ol>
  </section>
  <section class="q-block q-answer" aria-labelledby="q-ans-h">
    <h2 id="q-ans-h" class="q-h2">正答</h2>
    {ans_block}
  </section>
  <section class="q-block" aria-labelledby="q-exp-h">
    <h2 id="q-exp-h" class="q-h2">解説</h2>
    <div class="q-exp">{exp_html}</div>
  </section>
  <p class="q-app-link"><a href="{html.escape(root_idx)}">アプリで演習する</a></p>
</main>
{static_footer_block(rel_path)}
</body>
</html>
"""


def build_q_index(pages: list[dict], base_url: str) -> str:
    by_year: dict[int, list[dict]] = {}
    for p in pages:
        by_year.setdefault(p["year"], []).append(p)
    for y in by_year:
        by_year[y].sort(key=lambda x: x["qno"])

    year_blocks = []
    for y in sorted(by_year.keys()):
        links = []
        for p in by_year[y]:
            href = "/" + p["rel_path"]
            label = f"第{p['qno']}問"
            links.append(f'<li><a href="{html.escape(href)}">{html.escape(label)}</a></li>')
        year_blocks.append(
            f"<section class=\"q-year\"><h2>{y}年（{html.escape(by_year[y][0]['wareki'])}）</h2>"
            f"<ol class=\"q-year-list\">{''.join(links)}</ol></section>"
        )

    return f"""<!DOCTYPE html>
<html lang="ja">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>過去問一覧｜賃管マスター（賃貸不動産経営管理士）</title>
<meta name="description" content="賃貸不動産経営管理士試験の過去問を年度別に一覧するページです。">
<link rel="canonical" href="{html.escape(public_url(base_url, "q/index.html"))}">
<link rel="stylesheet" href="../site-pages.css">
</head>
<body class="q-static-body">
<header class="q-static-header">
  <p class="q-static-brand"><a href="../index.html">賃管マスター</a> · <a href="../terms/index.html">用語集</a> · <a href="../about.html">概要</a> · <a href="../privacy.html">プライバシー</a></p>
  <nav aria-label="パンくず"><ol class="q-breadcrumb">
    <li><a href="../index.html">トップ</a></li>
    <li aria-current="page">過去問一覧</li>
  </ol></nav>
</header>
<main class="q-static-main">
  <h1 class="q-h1">過去問一覧</h1>
  <p class="q-meta">全 {len(pages)} 問</p>
  {"".join(year_blocks)}
</main>
{static_footer_block(Path("q/index.html"))}
</body>
</html>
"""


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


def main() -> int:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--base-url", default=BASE_DEFAULT)
    args = ap.parse_args()
    base = args.base_url.rstrip("/")

    rows = load_rows()
    pages = [page_dict(r, i) for i, r in enumerate(rows, start=2)]

    if Q_ROOT.is_dir():
        shutil.rmtree(Q_ROOT)
    past_root = Q_ROOT / "past"
    for p in pages:
        rel = Path(p["rel_path"])
        out_file = ROOT / rel
        out_file.parent.mkdir(parents=True, exist_ok=True)
        html_out = build_question_html(p, out_file.relative_to(ROOT), base)
        out_file.write_text(html_out, encoding="utf-8")

    q_index = ROOT / "q" / "index.html"
    q_index.parent.mkdir(parents=True, exist_ok=True)
    q_index.write_text(build_q_index(pages, base), encoding="utf-8")

    urls = [
        f"{base}/",
        f"{base}/index.html",
        f"{base}/about.html",
        f"{base}/privacy.html",
        f"{base}/related-sites.html",
        f"{base}/articles/index.html",
        f"{base}/q/index.html",
    ]
    urls += [f"{base}/{p['rel_path']}" for p in pages]
    terms_dir = ROOT / "terms"
    if (terms_dir / "index.html").is_file():
        urls.append(f"{base}/terms/index.html")
    if terms_dir.is_dir():
        for p in sorted(terms_dir.glob("g-*.html")):
            urls.append(f"{base}/{p.relative_to(ROOT).as_posix()}")
    write_sitemap(urls, ROOT / "sitemap.xml")

    robots = ROOT / "robots.txt"
    robots.write_text(
        "User-agent: *\nAllow: /\n\nSitemap: "
        + f"{base}/sitemap.xml\n",
        encoding="utf-8",
    )

    print(f"Wrote {len(pages)} question pages under {past_root}")
    print(f"Wrote {q_index}")
    print(f"Wrote {ROOT / 'sitemap.xml'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
