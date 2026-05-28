#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Post-merge corrections for 賃管 numbers rows (S35–S44 verify fixes)."""

from __future__ import annotations

import json
import re
from typing import Any

from tools.hub_s35_s44_numbers_patches import SLUG_BASE_PATCHES, patch_for_slug

_BATCH_RE = re.compile(r"-num-s(3[5-9]|4[0-4])$")


def _title_for(base: str, batch: str) -> str | None:
    titles = {
        "nyukyosha-taiou": "入居者対応：法定義務と受託契約の整理",
        "nyukyo-trouble": "入居トラブル：初動対応と修繕義務",
        "chintai-kaitei": "賃料改定と更新料の数値整理",
        "kanri-houkoku": "管理業務報告：頻度と契約",
        "kanri-houkoku-sho": "管理報告書：頻度と契約",
        "keiyaku-shomen": "管理受託契約書面・重要事項説明",
        "keiyaku-koushin": "契約更新：更新料と法定更新",
    }
    t = titles.get(base)
    return f"{t}（{batch}）" if t else None


def apply_numbers_corrections(rows: list[dict[str, str]]) -> None:
    for row in rows:
        slug = row.get("slug", "")
        if not _BATCH_RE.search(slug):
            continue
        patch = patch_for_slug(slug)
        if not patch:
            continue
        base = slug.rsplit("-num-", 1)[0]
        batch = slug.rsplit("-", 1)[-1].upper()
        for key, val in patch.items():
            if key == "item_rows":
                row["item_rows"] = json.dumps(val, ensure_ascii=False)
            else:
                row[key] = val
        new_title = _title_for(base, batch)
        if new_title:
            row["title"] = new_title
            row["article_title"] = f"{new_title}｜数値早見"
        summary_theme = SLUG_BASE_PATCHES[base]["highlight"].split("。")[0]
        row["summary"] = f"{summary_theme}。借地借家法・賃管法・受託契約の関係を整理します。"
