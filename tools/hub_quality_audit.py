#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""知識ハブ CSV の品質監査（プロ水準・SEO観点の簡易チェック）."""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

CONCRETE = re.compile(
    r"\d|％|%|年|月|日|条|項|問|点|円|時間|義務|試験|法令|協議会|www"
)
GENERIC_PAD = "過去問の正誤肢と照合しながら復習"
MIN_LEAD, MIN_FAQ, TARGET_FAQ = 80, 100, 110


def audit_row(row: dict[str, str]) -> list[str]:
    issues: list[str] = []
    lead = row.get("article_lead", "")
    if len(lead) < MIN_LEAD:
        issues.append(f"thin_lead({len(lead)})")
    elif not CONCRETE.search(lead):
        issues.append("lead_no_concrete")
    for n in range(1, 5):
        a = row.get(f"faq_{n}_answer", "")
        if not a:
            issues.append(f"missing_faq{n}")
        elif len(a) < MIN_FAQ:
            issues.append(f"short_faq{n}({len(a)})")
        elif len(a) < TARGET_FAQ:
            issues.append(f"faq{n}_below_target({len(a)})")
        if GENERIC_PAD in a:
            issues.append(f"generic_pad_faq{n}")
    return issues


def main() -> int:
    data = ROOT / "data"
    total_issues = 0
    for fname in ("comparisons.csv", "numbers.csv", "mistakes.csv"):
        path = data / fname
        if not path.exists():
            continue
        with path.open(encoding="utf-8") as f:
            for i, row in enumerate(csv.DictReader(f), start=2):
                issues = audit_row(row)
                if issues:
                    total_issues += 1
                    print(f"{fname}:{i} {row.get('slug','')} -> {', '.join(issues)}")
    if total_issues == 0:
        print("quality audit: OK (no issues)")
        return 0
    print(f"quality audit: {total_issues} rows with issues")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
