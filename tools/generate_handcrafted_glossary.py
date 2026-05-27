#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate hand-crafted glossary JSON for all terms and apply to CSV."""

from __future__ import annotations

import csv
import json
import subprocess
import sys
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.glossary_craft_engine import craft_all

CSV_PATH = ROOT / "data" / "glossary_terms.csv"
CONTENT_DIR = ROOT / "data" / "glossary_handcraft_content"


def main() -> int:
    rows = list(csv.DictReader(CSV_PATH.read_text(encoding="utf-8-sig").splitlines()))
    crafted = craft_all(rows)

    CONTENT_DIR.mkdir(parents=True, exist_ok=True)
    by_cat: dict[str, dict[str, dict]] = defaultdict(dict)
    for row in rows:
        term = row["term"].strip()
        cat = row.get("category") or "その他"
        by_cat[cat][term] = crafted[term]

    for cat, payload in by_cat.items():
        safe = cat.replace("/", "_")
        path = CONTENT_DIR / f"{safe}.json"
        path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Wrote {len(crafted)} terms to {CONTENT_DIR} ({len(by_cat)} category files)")

    proc = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "apply_handcrafted_glossary.py")],
        cwd=ROOT,
    )
    if proc.returncode != 0:
        return proc.returncode

    proc2 = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "build_glossary_pages.py")],
        cwd=ROOT,
    )
    return proc2.returncode


if __name__ == "__main__":
    raise SystemExit(main())
