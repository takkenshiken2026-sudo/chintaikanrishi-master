#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知識ハブ CSV の summary 列を、詳細記事ベースの要約文に一括更新する。"""

from __future__ import annotations

import argparse
import csv
import io
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.index_summary import (  # noqa: E402
    compare_index_overview,
    is_boilerplate_overview,
    mistakes_index_overview,
    numbers_index_overview,
)

HUB_CSV = {
    "compare": (ROOT / "data" / "comparisons.csv", compare_index_overview),
    "numbers": (ROOT / "data" / "numbers.csv", numbers_index_overview),
    "mistakes": (ROOT / "data" / "mistakes.csv", mistakes_index_overview),
}


def enrich_csv(path: Path, overview_fn, *, dry_run: bool) -> tuple[int, int]:
    text = path.read_text(encoding="utf-8-sig")
    rows = list(csv.DictReader(io.StringIO(text)))
    if not rows:
        return 0, 0
    fieldnames = list(rows[0].keys())
    changed = 0
    for row in rows:
        old = (row.get("summary") or "").strip()
        new = overview_fn(row).strip()
        if not new or new == old:
            continue
        if not is_boilerplate_overview(old) and len(old) >= len(new):
            continue
        row["summary"] = new
        changed += 1
    if changed and not dry_run:
        out = io.StringIO()
        writer = csv.DictWriter(out, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)
        path.write_text(out.getvalue(), encoding="utf-8")
    return len(rows), changed


def main() -> int:
    ap = argparse.ArgumentParser(description="Update hub CSV summary columns from article content.")
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--type", choices=("compare", "numbers", "mistakes", "all"), default="all")
    args = ap.parse_args()

    kinds = list(HUB_CSV) if args.type == "all" else [args.type]
    total_changed = 0
    for kind in kinds:
        path, fn = HUB_CSV[kind]
        n, changed = enrich_csv(path, fn, dry_run=args.dry_run)
        print(f"{kind}: {changed}/{n} summary rows updated" + (" (dry-run)" if args.dry_run else ""))
        total_changed += changed
    return 0 if total_changed >= 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
