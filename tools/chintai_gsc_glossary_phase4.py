#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase4: GSC上位用語の seo_title / meta_description 強化。"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

PATCHES: dict[str, dict[str, str]] = {
    "シェアハウス": {
        "article_title": "シェアハウスとは？賃管試験の定義·ルームシェアとの違い",
        "article_lead": (
            "「シェアハウス」は個室を貸し共用部分を共有する賃貸形態です。"
            "賃管試験では運営方式ごとの契約主体·35条書面·ルームシェアとの違いが頻出します。"
            "定義·関連語·演習の進め方を具体例付きで整理します。"
        ),
    },
    "解除の将来効": {
        "article_title": "将来効とは？賃管試験·解除の将来効（民法620条）",
        "article_lead": (
            "検索の「将来効とは」は、賃貸借の解除が遡及せず将来にのみ効く原則（解除の将来効·民法620条）を指します。"
            "使用収益の有効·解除手続との違いを賃管試験向けに具体例付きで解説します。"
        ),
    },
    "必要経費": {
        "article_title": "必要経費とは？賃管試験·不動産所得の控除と修繕費の区分",
        "article_lead": (
            "必要経費は所得を得るための支出で控除可能（所得税法37条）。"
            "賃管試験では修繕費と資本的支出の区分·不動産所得の典型例が問われます。"
            "定義·条文·誤答パターンを具体例付きで整理します。"
        ),
    },
    "近傍同種建物の賃料": {
        "article_title": "近傍同種とは？賃料増減請求の判断要素（借地借家法32条）",
        "article_lead": (
            "「近傍同種」は賃料増減請求で参照する近隣の同種建物の賃料水準です。"
            "賃管試験ではエリア·グレード比較と鑑定評価との関係が頻出します。"
            "借地借家法32条の要件を具体例付きで解説します。"
        ),
    },
    "バリアフリー": {
        "article_title": "バリアフリーとは？賃管試験·新法と高齢者向け賃貸の設備要件",
        "article_lead": (
            "バリアフリーは生活上の障壁を除く設計·設備です。"
            "賃管試験ではバリアフリー新法·サ高住との違い·段差·幅員など設備分野の論点が問われます。"
            "定義と頻出の落とし穴を具体例付きで整理します。"
        ),
    },
}


def main() -> int:
    csv_path = ROOT / "data" / "glossary_terms.csv"
    rows = list(csv.DictReader(csv_path.open(encoding="utf-8-sig")))
    patched = 0
    for row in rows:
        term = (row.get("term") or "").strip()
        if term not in PATCHES:
            continue
        row.update(PATCHES[term])
        patched += 1
    if patched:
        with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
            w = csv.DictWriter(f, fieldnames=rows[0].keys(), lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
    print(f"patched {patched} glossary terms")
    return 0 if patched == len(PATCHES) else 1


if __name__ == "__main__":
    raise SystemExit(main())
