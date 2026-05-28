#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""賃管 知識ハブ CSV 統合出力（S30 + S31 …）."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.write_chintai_hub_s30 import DATA, HEADER_COMPARE, HEADER_MISTAKES, HEADER_NUMBERS  # noqa: E402
from tools.write_chintai_hub_s30_content import COMPARISONS as C30, MISTAKES as M30, NUMBERS as N30  # noqa: E402
from tools.write_chintai_hub_s31_content import (  # noqa: E402
    COMPARISONS_ADD,
    MISTAKES_ADD,
    NUMBERS_ADD,
)


def _merge(*groups: list[dict]) -> list[dict]:
    seen: set[str] = set()
    out: list[dict] = []
    for group in groups:
        for row in group:
            slug = row["slug"]
            if slug in seen:
                raise ValueError(f"duplicate slug: {slug}")
            seen.add(slug)
            out.append(row)
    return out


def write_csv(path: Path, header: list[str], rows: list[dict]) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=header, lineterminator="\n")
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    comparisons = _merge(C30, COMPARISONS_ADD)
    numbers = _merge(N30, NUMBERS_ADD)
    mistakes = _merge(M30, MISTAKES_ADD)
    write_csv(DATA / "comparisons.csv", HEADER_COMPARE, comparisons)
    write_csv(DATA / "numbers.csv", HEADER_NUMBERS, numbers)
    write_csv(DATA / "mistakes.csv", HEADER_MISTAKES, mistakes)
    print(f"wrote compare={len(comparisons)} numbers={len(numbers)} mistakes={len(mistakes)}")


if __name__ == "__main__":
    main()
