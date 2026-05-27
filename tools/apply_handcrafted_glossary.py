#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Merge hand-crafted glossary article JSON into data/glossary_terms.csv."""

from __future__ import annotations

import csv
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CSV_PATH = ROOT / "data" / "glossary_terms.csv"
CONTENT_DIR = ROOT / "data" / "glossary_handcraft_content"

from tools.glossary_craft_engine import craft_from_append  # noqa: E402

DETAIL_COLS = [
    "article_title",
    "article_lead",
    "term_detail_body",
    "exam_points",
    "common_mistakes",
    "memory_tip",
    "example_question",
    "example_answer",
    "faq_1_question",
    "faq_1_answer",
    "faq_2_question",
    "faq_2_answer",
    "faq_3_question",
    "faq_3_answer",
    "faq_4_question",
    "faq_4_answer",
    "summary_body",
    "comparison_table",
    "exam_focus",
    "explanation",
]


def load_handcrafted() -> dict[str, dict[str, str]]:
    merged: dict[str, dict[str, str]] = {}
    if not CONTENT_DIR.is_dir():
        return merged
    for path in sorted(CONTENT_DIR.glob("*.json")):
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict):
            continue
        for term, payload in data.items():
            if isinstance(payload, dict):
                merged[term.strip()] = payload
    return merged


def normalize_payload(term: str, payload: dict) -> dict[str, str]:
    out: dict[str, str] = {}
    if isinstance(payload.get("exam_points"), list):
        out["exam_points"] = ";".join(str(x).strip() for x in payload["exam_points"] if str(x).strip())
    for key, val in payload.items():
        if key == "exam_points":
            continue
        if val is None:
            continue
        out[key] = str(val).strip()
    if not out.get("article_title"):
        out["article_title"] = f"{term}とは？意味・試験ポイントを整理"
    if not out.get("explanation") and out.get("exam_points"):
        pts = out["exam_points"].split(";")
        short = out.get("short_def") or ""
        out["explanation"] = (
            f"{term}は、{short.rstrip('。')}。"
            f"試験では{pts[0]}を問われやすいため、関連用語との違いも確認してください。"
        )
    return out


def main() -> int:
    handcrafted = load_handcrafted()
    if not handcrafted:
        print(f"No JSON in {CONTENT_DIR}", file=sys.stderr)
        return 1

    rows = list(csv.DictReader(CSV_PATH.read_text(encoding="utf-8-sig").splitlines()))
    fieldnames = list(rows[0].keys()) if rows else []
    for col in DETAIL_COLS:
        if col not in fieldnames:
            fieldnames.append(col)

    applied = 0
    missing_terms: list[str] = []
    append_override = 0
    for row in rows:
        term = row["term"].strip()
        payload = handcrafted.get(term)
        if not payload:
            missing_terms.append(term)
            continue
        normalized = normalize_payload(term, payload)
        for key, val in normalized.items():
            if val:
                row[key] = val
        applied += 1

        # Curated rows in append_glossary_50_terms.py take precedence
        curated = craft_from_append(row)
        if curated:
            for key, val in curated.items():
                if val:
                    row[key] = val
            append_override += 1

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(f"Applied handcrafted content for {applied}/{len(rows)} terms")
    print(f"Append glossary overrides (higher quality): {append_override}")
    if missing_terms:
        print(f"Missing handcrafted entries: {len(missing_terms)}")
        for t in missing_terms[:20]:
            print(f"  - {t}")
        if len(missing_terms) > 20:
            print(f"  ... and {len(missing_terms) - 20} more")
    return 0 if not missing_terms else 2


if __name__ == "__main__":
    raise SystemExit(main())
