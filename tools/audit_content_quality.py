#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Audit public HTML/CSV for typos, duplicate chars, awkward text, and content errors."""

from __future__ import annotations

import csv
import re
import sys
from dataclasses import dataclass
from html import unescape
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Strip tags for text analysis
TAG_RE = re.compile(r"<[^>]+>")
SCRIPT_STYLE_RE = re.compile(r"<(script|style)[^>]*>.*?</\1>", re.I | re.S)

# Suspicious duplicate kana/kanji (3+ same char) — exclude intentional ellipsis
DUP_CHAR_RE = re.compile(
    r"([\u3040-\u9fff\u30a0-\u30ff\u3400-\u4dbf])\1{2,}"
)

# Common exam-site typos / wrong expressions
TYPO_PATTERNS: list[tuple[str, re.Pattern[str], str]] = [
    ("重複助詞「のの」", re.compile(r"のの"), "「のの」"),
    ("重複助詞「をを」", re.compile(r"をを"), "「をを」"),
    ("重複助詞「がが」", re.compile(r"がが"), "「がが」"),
    ("重複助詞「にに」", re.compile(r"にに"), "「にに」"),
    ("重複助詞「はは」", re.compile(r"はは"), "「はは」"),
    ("重複助詞「とと」", re.compile(r"とと"), "「とと」"),
    ("重複助詞「もも」", re.compile(r"もも"), "「もも」"),
    ("重複「等等」", re.compile(r"等等"), "「等等」"),
    ("重複「事事」", re.compile(r"事事"), "「事事」"),
    ("重複「法法」", re.compile(r"法法"), "「法法」"),
    ("重複「契約約」", re.compile(r"契約約"), "「契約約」"),
    ("重複「管理理」", re.compile(r"管理理"), "「管理理」"),
    ("半角スペース連続", re.compile(r"  +"), "連続半角スペース"),
    ("全角スペース連続", re.compile(r"\u3000{2,}"), "連続全角スペース"),
    ("HTML実体参照の未解決", re.compile(r"&amp;amp;|&lt;&lt;|&gt;&gt;"), "二重エスケープ"),
    ("プレースホルダ残存", re.compile(r"TODO|FIXME|XXX|TBD|（要確認）|（仮）"), "プレースホルダ"),
    ("テンプレ残存", re.compile(r"サンプル記事|ダミー|lorem ipsum", re.I), "テンプレ文"),
    ("誤「適切で適切」", re.compile(r"適切で適切"), "重複表現"),
    ("誤「以下の以下の」", re.compile(r"以下の以下の"), "重複表現"),
    ("誤「記述の記述」", re.compile(r"記述の記述"), "重複表現"),
    ("誤「についてについて」", re.compile(r"についてについて"), "重複表現"),
    ("誤「場合場合」", re.compile(r"場合場合"), "重複表現"),
    ("誤「必要必要」", re.compile(r"必要必要"), "重複表現"),
    ("誤「義務務」", re.compile(r"義務務"), "重複表現"),
    ("誤「賃貸貸」", re.compile(r"賃貸貸"), "重複表現"),
    ("誤「借主主」", re.compile(r"借主主"), "重複表現"),
    ("誤「貸主主」", re.compile(r"貸主主"), "重複表現"),
]

# Whitelist: intentional repeated chars in legal terms
DUP_WHITELIST = frozenset(
    {
        "々", "〻", "…", "。。",
        "母母",  # rare but skip if in names
    }
)

PUBLIC_GLOBS = [
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

CSV_FILES = [
    "data/glossary_terms.csv",
    "data/guide_articles.csv",
    "data/past_questions_marubatsu_all_explanations.csv",
    "data/practice_questions.csv",
    "data/ichimon_questions.csv",
]


@dataclass
class Issue:
    level: str
    source: str
    message: str

    def format(self) -> str:
        return f"[{self.level}] {self.source} - {self.message}"


def strip_html(text: str) -> str:
    text = SCRIPT_STYLE_RE.sub(" ", text)
    text = TAG_RE.sub(" ", text)
    return unescape(text)


def collect_files() -> list[Path]:
    out: list[Path] = []
    for pattern in PUBLIC_GLOBS:
        out.extend(sorted(ROOT.glob(pattern)))
    seen: set[Path] = set()
    unique: list[Path] = []
    for p in out:
        r = p.resolve()
        if r not in seen and p.is_file():
            seen.add(r)
            unique.append(p)
    return unique


def scan_text(source: str, text: str, issues: list[Issue], *, in_csv: bool = False) -> None:
    for label, pattern, detail in TYPO_PATTERNS:
        for m in pattern.finditer(text):
            start = max(0, m.start() - 20)
            end = min(len(text), m.end() + 20)
            snippet = text[start:end].replace("\n", " ")
            issues.append(
                Issue("ERROR", source, f"{label}: {detail} …{snippet}…")
            )

    for m in DUP_CHAR_RE.finditer(text):
        ch = m.group(1)
        frag = m.group(0)
        if frag in DUP_WHITELIST:
            continue
        # Skip common intentional: 々 is handled separately
        if ch == "ー" and len(frag) <= 3:
            continue
        start = max(0, m.start() - 15)
        end = min(len(text), m.end() + 15)
        snippet = text[start:end].replace("\n", " ")
        issues.append(
            Issue("WARN", source, f"同一文字3連続「{frag}」: …{snippet}…")
        )

    # Empty visible headings in HTML
    if not in_csv:
        for hm in re.finditer(r"<h[1-6][^>]*>\s*</h[1-6]>", text, re.I):
            issues.append(Issue("ERROR", source, "空の見出しタグ"))


def scan_html(path: Path, issues: list[Issue]) -> None:
    text = path.read_text(encoding="utf-8")
    scan_text(str(path.relative_to(ROOT)), strip_html(text), issues)
    scan_text(str(path.relative_to(ROOT)), text, issues)

    # Duplicate consecutive paragraphs (sign of copy-paste error)
    paras = re.findall(r"<p[^>]*>(.*?)</p>", text, re.I | re.S)
    cleaned = [re.sub(r"\s+", " ", unescape(TAG_RE.sub("", p))).strip() for p in paras]
    cleaned = [p for p in cleaned if len(p) > 40]
    for i in range(1, len(cleaned)):
        if cleaned[i] == cleaned[i - 1]:
            issues.append(
                Issue(
                    "ERROR",
                    str(path.relative_to(ROOT)),
                    f"連続する同一段落（{cleaned[i][:50]}…）",
                )
            )


def scan_csv(path: Path, issues: list[Issue]) -> None:
    rel = str(path.relative_to(ROOT))
    with path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row_num, row in enumerate(reader, start=2):
            for col, val in row.items():
                if not val or col.startswith("_"):
                    continue
                scan_text(f"{rel}:{row_num}:{col}", val, issues, in_csv=True)


def main() -> int:
    issues: list[Issue] = []

    for pattern in PUBLIC_GLOBS:
        pass  # collect via collect_files

    files = collect_files()
    if not files:
        print("No files to audit", file=sys.stderr)
        return 1

    for path in files:
        scan_html(path, issues)

    for csv_rel in CSV_FILES:
        csv_path = ROOT / csv_rel
        if csv_path.is_file():
            scan_csv(csv_path, issues)

    errors = [i for i in issues if i.level == "ERROR"]
    warns = [i for i in issues if i.level == "WARN"]

    for issue in sorted(issues, key=lambda i: (i.level, i.source)):
        print(issue.format())

    print(
        f"\nContent audit: {len(files)} HTML, {len(errors)} error(s), {len(warns)} warning(s)",
        file=sys.stderr if errors else sys.stdout,
    )
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
