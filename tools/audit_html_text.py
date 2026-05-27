#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Scan public HTML/CSV for typos, duplicate chars, and broken prose."""

from __future__ import annotations

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from html import unescape
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Known typos seen on sibling exam sites (賃管向け)
KNOWN_TYPOS: tuple[tuple[str, str], ...] = (
    ("試騲", "試験"),
    ("実践演錇", "実践演習"),
    ("賃貸借借", "賃貸借"),
    ("管理管理", "管理"),
    ("契約約", "契約"),
    ("法令令", "法令"),
    ("賃料料", "賃料"),
    ("原状状", "原状"),
    ("YOUR-DOMAIN", "プレースホルダドメイン"),
    ("Sampleマスター", "サンプルサイト名"),
    ("【記入】", "未執筆マーカー"),
    ("差し替えてください", "差し替え指示"),
)

# Allow intentional doubles (叠字)
ALLOWED_DOUBLES = frozenset(
    "々ー…・。、）)」』】］>」"
)

HTML_GLOBS = [
    "index.html",
    "about.html",
    "privacy.html",
    "related-sites.html",
    "articles/index.html",
    "articles/*/index.html",
    "terms/index.html",
    "terms/field-*/index.html",
    "terms/g-*.html",
    "q/index.html",
    "q/past/**/index.html",
    "q/practice/**/index.html",
    "q/ichimon/**/index.html",
]

CSV_TEXT_COLS = {
    ROOT / "data" / "glossary_terms.csv": (
        "term",
        "short_def",
        "definition",
        "explanation",
        "article_lead",
        "term_detail_body",
        "common_mistakes",
        "memory_tip",
        "example_question",
        "faq_1_answer",
        "faq_2_answer",
        "faq_3_answer",
        "faq_4_answer",
    ),
    ROOT / "data" / "guide_articles.csv": (
        "title",
        "meta_description",
        "lead",
        *(f"section_{n}_body" for n in range(1, 8)),
        *(f"faq_{n}_answer" for n in range(1, 4)),
    ),
    ROOT / "data" / "past_questions.csv": (
        "stem_plain",
        "explanation",
        "explanation_summary",
        "explanation_correct",
        "explanation_choices",
        "explanation_point",
    ),
}


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._skip = 0
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs) -> None:
        if tag in ("script", "style", "noscript"):
            self._skip += 1

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style", "noscript") and self._skip:
            self._skip -= 1

    def handle_data(self, data: str) -> None:
        if self._skip:
            return
        t = data.strip()
        if t:
            self.parts.append(t)


def strip_html(text: str) -> str:
    parser = TextExtractor()
    try:
        parser.feed(text)
        parser.close()
    except Exception:
        return unescape(re.sub(r"<[^>]+>", " ", text))
    return unescape(" ".join(parser.parts))


def duplicate_char_issues(text: str) -> list[str]:
    issues: list[str] = []
    # 同一漢字・かなが3回以上連続（「々」除く）
    for m in re.finditer(r"([\u3040-\u9fff])\1{2,}", text):
        ch = m.group(1)
        if ch in ALLOWED_DOUBLES:
            continue
        issues.append(f"重複文字「{ch*3}…」")
    # 助詞・接続の異常連続
    for pat, msg in (
        (r"は、{2,}", "「は、」の連続"),
        (r"。{3,}", "句点の過剰連続"),
        (r"(\w+)は、\1は", "主語の二重開始"),
    ):
        if re.search(pat, text):
            issues.append(msg)
    return issues


def broken_prose_issues(text: str) -> list[str]:
    issues: list[str] = []
    if re.search(r"[。！？][、,]", text):
        issues.append("句読点の順序が不自然")
    if re.search(r"^\s*[、,]", text):
        issues.append("文頭が読点")
    if "。。" in text and "……" not in text:
        issues.append("句点二重")
    if re.search(r"\(\s*\)|（\s*）", text):
        issues.append("空括弧")
    return issues


@dataclass
class Finding:
    level: str
    source: str
    check: str
    message: str
    snippet: str = ""


def collect_html() -> list[Path]:
    out: list[Path] = []
    seen: set[Path] = set()
    for pattern in HTML_GLOBS:
        for path in sorted(ROOT.glob(pattern)):
            rp = path.resolve()
            if rp not in seen and path.is_file():
                seen.add(rp)
                out.append(path)
    return out


def scan_text(source: str, text: str, findings: list[Finding]) -> None:
    if not text or len(text) < 4:
        return
    for typo, label in KNOWN_TYPOS:
        if typo in text:
            idx = text.index(typo)
            findings.append(
                Finding(
                    "error",
                    source,
                    "typo",
                    f"{label}（{typo!r}）",
                    text[max(0, idx - 20) : idx + len(typo) + 20],
                )
            )
    for msg in duplicate_char_issues(text):
        findings.append(Finding("warn", source, "duplicate_char", msg, text[:80]))
    for msg in broken_prose_issues(text):
        findings.append(Finding("warn", source, "prose", msg, text[:80]))


def scan_html(path: Path, findings: list[Finding]) -> None:
    rel = str(path.relative_to(ROOT))
    raw = path.read_text(encoding="utf-8", errors="replace")
    scan_text(rel, strip_html(raw), findings)
    if 'href=""' in raw or "href=''" in raw:
        findings.append(Finding("error", rel, "empty_href", "空の href 属性"))


def scan_csv(path: Path, cols: tuple[str, ...], findings: list[Finding]) -> None:
    if not path.is_file():
        return
    rows = list(csv.DictReader(path.open(encoding="utf-8-sig")))
    for i, row in enumerate(rows, start=2):
        label = row.get("term") or row.get("slug") or row.get("question_no") or str(i)
        for col in cols:
            text = (row.get(col) or "").strip()
            if not text:
                continue
            scan_text(f"{path.name}:{i}:{col}({label})", text, findings)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="WARN も失敗扱い")
    args = ap.parse_args()

    findings: list[Finding] = []
    files = collect_html()
    for path in files:
        scan_html(path, findings)

    for csv_path, cols in CSV_TEXT_COLS.items():
        scan_csv(csv_path, cols, findings)

    errors = [f for f in findings if f.level == "error"]
    warns = [f for f in findings if f.level == "warn"]

    print(f"HTML/CSV text audit: {len(files)} HTML file(s)")
    print(f"ERROR {len(errors)} / WARN {len(warns)}")

    for item in errors[:50]:
        print(f"  [E] {item.source} [{item.check}] {item.message}")
        if item.snippet:
            print(f"      …{item.snippet}…")
    for item in warns[:30]:
        print(f"  [W] {item.source} [{item.check}] {item.message}")

    if len(errors) > 50:
        print(f"  … ERROR 他 {len(errors)-50} 件")
    if len(warns) > 30:
        print(f"  … WARN 他 {len(warns)-30} 件")

    if errors:
        return 1
    if args.strict and warns:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
