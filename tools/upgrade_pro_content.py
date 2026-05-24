#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Run pro-writer upgrades for glossary + guides, then rebuild pages."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, cwd=ROOT, check=True)


def main() -> int:
    py = sys.executable
    run([py, "tools/glossary_pro_writer.py"])
    run([py, "tools/guide_pro_writer.py"])
    run([py, "tools/build_glossary_pages.py"])
    run([py, "tools/build_article_pages.py"])
    run([py, "tools/validate_csv.py"])
    print("Pro content upgrade complete. Run build_all.py for full site if needed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
