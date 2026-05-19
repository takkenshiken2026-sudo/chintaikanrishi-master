# -*- coding: utf-8 -*-
"""賃管マスター向けサイト設定（試験ガイド記事ビルド用）。"""

from __future__ import annotations

SITE_ORIGIN = "https://chintaikanrishi-master.jp"
BRAND_NAME = "賃管マスター"
BRAND_MARK = "賃管"
EXAM_NAME = "賃貸不動産経営管理士試験"
OFFICIAL_ORG = "賃貸不動産経営管理士協議会"


def clean_origin() -> str:
    return SITE_ORIGIN.rstrip("/")


def brand_name() -> str:
    return BRAND_NAME


def brand_mark() -> str:
    return BRAND_MARK


def exam_name() -> str:
    return EXAM_NAME


def official_organization() -> str:
    return OFFICIAL_ORG


def external_links() -> list[dict[str, str]]:
    return [
        {
            "url": "https://www.chintaikanrishi.jp/",
            "label": "賃貸不動産経営管理士協議会（公式）",
            "description": "試験日程・要項・合格発表・登録制度の公式情報",
        },
        {
            "url": "https://www.mlit.go.jp/jutakukentiku/house/",
            "label": "国土交通省 住宅局",
            "description": "賃貸住宅管理業法や住宅政策の背景理解に役立ちます",
        },
    ]


def primary_external_link() -> dict[str, str]:
    links = external_links()
    return links[0] if links else {"url": "https://www.chintaikanrishi.jp/", "label": OFFICIAL_ORG, "description": ""}
