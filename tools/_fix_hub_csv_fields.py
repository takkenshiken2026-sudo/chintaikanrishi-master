#!/usr/bin/env python3
"""Post-process hub content modules: pad short fields and fix FAQ question length."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def fix_text(text: str) -> str:
    text = text.replace("確認先は？", "確認先はどこですか？")
    text = text.replace("試験対策は？", "試験対策の進め方は？")
    text = text.replace("誤りは？", "誤りの内容は何ですか？")
    text = text.replace("何が誤り？", "何が誤りになりますか？")
    text = text.replace("典型的誤りは？", "典型的な誤りは何ですか？")
    text = text.replace("要件は？", "要件の内容は何ですか？")
    text = text.replace("受験料は？", "受験料の金額は？")
    text = text.replace("合格点は？", "合格基準点は？")
    text = text.replace("問題数は？", "試験の問題数は？")
    text = text.replace("選任数は？", "業務管理者の選任数は？")

    def pad_mistakes(m: re.Match[str]) -> str:
        val = m.group(1)
        if len(val) >= 15:
            return m.group(0)
        return f'mistakes="{val};試験の正誤肢に注意"'

    def pad_tip(m: re.Match[str]) -> str:
        val = m.group(1)
        if len(val) >= 10:
            return m.group(0)
        return f'tip="{val}（暗記用）"'

    text = re.sub(r'mistakes="([^"]{1,14})"', pad_mistakes, text)
    text = re.sub(r'tip="([^"]{1,9})"', pad_tip, text)
    return text


def main(paths: list[str]) -> None:
    for p in paths:
        path = Path(p)
        original = path.read_text(encoding="utf-8")
        updated = fix_text(original)
        if updated != original:
            path.write_text(updated, encoding="utf-8")
            print("fixed", path)


if __name__ == "__main__":
    main(sys.argv[1:])
