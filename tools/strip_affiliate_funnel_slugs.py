#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Remove funnel references to unpublished affiliate slugs from guide_articles.csv."""

from __future__ import annotations

import argparse
import csv
import re
import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TEXT_COLUMNS = tuple(
    f"section_{n}_body" for n in range(1, 8)
) + ("lead", "meta_description", "user_intent") + tuple(
    f"faq_{n}_answer" for n in range(1, 6)
)


def split_semicolon(value: str) -> list[str]:
    return [x.strip() for x in (value or "").split(";") if x.strip()]


def join_semicolon(items: list[str]) -> str:
    return ";".join(items)


def strip_related_links(related: str, slug: str) -> str:
    kept = []
    for item in split_semicolon(related):
        target = item.split(":", 1)[0].strip()
        if target == slug:
            continue
        kept.append(item)
    return join_semicolon(kept)


def strip_text_refs(text: str, slug: str) -> str:
    if not text or slug not in text:
        return text
    out = text
    out = re.sub(
        rf"\[[^\]]*\]\(\.\./{re.escape(slug)}/\)[^。]*。?",
        "",
        out,
    )
    out = re.sub(rf"[^。]*{re.escape(slug)}[^。]*。", "", out)
    out = re.sub(r"。{2,}", "。", out)
    return out.strip()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--slugs",
        required=True,
        help="Comma-separated affiliate slugs to strip (e.g. affiliate-free-vs-paid-study)",
    )
    args = parser.parse_args()
    slugs = [s.strip() for s in args.slugs.split(",") if s.strip()]
    if not slugs:
        print("ERROR: no slugs", file=sys.stderr)
        return 1

    csv_path = ROOT / "data" / "guide_articles.csv"
    rows: list[dict[str, str]] = []
    touched = 0

    with csv_path.open(encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        if not fieldnames:
            print("ERROR: empty CSV", file=sys.stderr)
            return 1
        for row in reader:
            changed = False
            for slug in slugs:
                new_related = strip_related_links(row.get("related_links", ""), slug)
                if new_related != row.get("related_links", ""):
                    row["related_links"] = new_related
                    changed = True
                for col in TEXT_COLUMNS:
                    if col not in row:
                        continue
                    new_text = strip_text_refs(row.get(col, ""), slug)
                    if new_text != row.get(col, ""):
                        row[col] = new_text
                        changed = True
            if changed:
                touched += 1
            rows.append(row)

    orig_lines = sum(1 for _ in csv_path.open(encoding="utf-8-sig"))
    fd, tmp = tempfile.mkstemp(suffix=".csv", dir=csv_path.parent)
    try:
        with open(fd, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
            writer.writeheader()
            writer.writerows(rows)
        new_lines = sum(1 for _ in open(tmp, encoding="utf-8"))
        if new_lines != orig_lines:
            print(f"ERROR: line count {orig_lines} -> {new_lines}", file=sys.stderr)
            return 1
        shutil.move(tmp, csv_path)
    finally:
        if Path(tmp).exists():
            Path(tmp).unlink()

    print(f"OK: stripped {slugs} from {touched} guide rows")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
