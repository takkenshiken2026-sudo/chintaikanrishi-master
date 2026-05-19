#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""コンテンツ生成の一括実行（CSV → 静的HTML）。"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

STEPS = [
    ("write_guide_articles_csv", [sys.executable, "tools/write_guide_articles_csv.py"]),
    ("build_article_pages", [sys.executable, "tools/build_article_pages.py"]),
    ("build_glossary_pages", [sys.executable, "tools/build_glossary_pages.py"]),
]


def main() -> int:
    for name, cmd in STEPS:
        print(f"=== {name} ===")
        r = subprocess.run(cmd, cwd=ROOT)
        if r.returncode != 0:
            print(f"Failed: {name}", file=sys.stderr)
            return r.returncode
    print("All steps completed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
