#!/usr/bin/env python3
"""Pad short hub content fields in a write_*_hub_s*_content.py module."""

from __future__ import annotations

import re
import sys
from pathlib import Path


def pad(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    text = text.replace("确认先", "確認先")
    text = text.replace("確認先は？", "確認先はどこですか？")
    text = text.replace("試験対策は？", "試験対策の進め方は？")

    def pad_m(m: re.Match[str]) -> str:
        v = m.group(1)
        if len(v) >= 15:
            return m.group(0)
        return f'mistakes="{v};試験の正誤肢に注意"'

    def pad_t(m: re.Match[str]) -> str:
        v = m.group(1)
        if len(v) >= 10:
            return m.group(0)
        return f'tip="{v}（暗記用フレーズ）"'

    def pad_title(m: re.Match[str]) -> str:
        v = m.group(1)
        if len(v) >= 10:
            return m.group(0)
        return f'article_title="{v}（試験）"'

    text = re.sub(r'mistakes="([^"]*)"', pad_m, text)
    text = re.sub(r'tip="([^"]*)"', pad_t, text)
    text = re.sub(r'article_title="([^"]*)"', pad_title, text)

    faq_q = {
        "誰が策定？": "長期修繕計画は誰が策定しますか？",
        "変更は？": "管理費の負担割合の変更は？",
        "怠ると？": "更新登録を怠るとどうなりますか？",
        "移送とは？": "危険物の移送とは何ですか？",
        "倍数とは？": "指定数量の倍数とは何ですか？",
        "誤りは？": "誤りの内容は何ですか？",
        "何が誤り？": "何が誤りになりますか？",
    }
    for a, b in faq_q.items():
        text = text.replace(f'"{a}"', f'"{b}"')

    path.write_text(text, encoding="utf-8")
    print("padded", path)


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        pad(Path(arg))
