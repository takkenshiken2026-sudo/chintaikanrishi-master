#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""published ガイドの section5 2列比較を差し替える OVERRIDES を生成。"""

from __future__ import annotations

import csv
import re
import textwrap
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import sys

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def has_s5_2col(row: dict) -> bool:
    h = row.get("section_5_heading") or ""
    b = row.get("section_5_body") or ""
    return "2列比較" in h or "| 本記事 |" in b or "| 本記事（" in b


def topic_from_row(row: dict) -> str:
    title = (row.get("title") or row.get("slug") or "").split("【")[0]
    title = re.sub(r"^賃管試験[·・]?", "", title)
    title = re.sub(r"^賃貸不動産経営管理士試験[·・]?", "", title)
    return title.strip() or row["slug"]


def make_s5(topic: str, slug: str) -> dict[str, str]:
    heading = f"{topic}で避けたい失敗" if len(topic) < 28 else "試験対策で避けたい失敗"
    intro = (
        f"{topic}は手順を飛ばして教材だけ増やすと、50問·120分·3分野の記録が残らず改善が遅れます。"
        if not slug.startswith("affiliate-")
        else f"{topic}は比較表だけ見て購入すると、要項改定年度や3分野の厚みを見落としやすくなります。"
    )
    bullets = [
        ("要項を開かずに学習開始", "11/15試験日·9/30締切·合格基準が曖昧なまま"),
        ("3分野を同量のまま固定", "契約·実務12/15が続いても配分を変えない"),
        ("50問通しを試験直前だけ", "120分配分の練習が不足する"),
        ("誤答理由を記録しない", "解き直し日が入らず再発が増える"),
    ]
    if "過去問" in topic or "past" in slug:
        bullets[0] = ("年度数だけを増やす", "弱点論点の解き直しが追いつかない")
    if "テキスト" in topic or "textbook" in slug or "affiliate" in slug:
        bullets[0] = ("収録年度を未確認", "要項出題範囲と目次がズレる")
        bullets[1] = ("2冊同時に開く", "完走率が下がり復習が分散する")
    body = intro + "\n\n" + "\n".join(f"**{a}** … {b}" for a, b in bullets)
    body += (
        "\n\nたとえば6月14日（日）に要項5項目を1枚メモし、6月21日（日）に3分野演習15問で正答数を記録、"
        "契約·実務が12/15未満なら翌週からその分野に週+2時間振り替えると、数字で計画が動きます。"
    )
    rev = "2026-06-18: GSC section5差し替え Phase3（2列比較撤去）"
    if slug.startswith("affiliate-"):
        rev = "2026-06-18: GSC section5差し替え Phase3（アフィリエイト・2列比較撤去）"
    return {
        "section_5_heading": heading,
        "section_5_body": body,
        "revision_note": rev,
    }


PHASE1_META: dict[str, str] = {
    "weight-by-topic": "賃管試験の分野別優先順位。8/16正答率·最弱分野+2時間·35/50目安と週次配分の具体例を解説します。",
    "exam-difficulty": "賃貸不動産経営管理士試験の難易度。統計·合格基準·演習3軸で判断する手順と50問通しの目安を具体例付き解説します。",
    "affiliate-textbooks-recommend": "賃管試験のおすすめテキスト3選。要項照合·3分野目次·週次配分とAmazon比較の選び方を具体例付き解説します。",
    "textbook-selection": "賃管試験のテキスト選び。6/14要項照合·基本1冊固定·弱点補助と乗り換え基準を具体例付き解説します。",
    "past-questions-how-to-use": "賃管試験の過去問の使い方。50問120分·分野別15問·誤答3語記録と1週間後の解き直しを解説します。",
    "pass-rate": "賃管試験の合格率·公表統計の読み方。3点セットと自分の演習データの分離·週次正答率の記録方法を解説します。",
    "pass-score": "賃管試験の合格点·35/50目安。要項の合格基準と分野別足切りの確認手順を具体例付き解説します。",
    "law-subject": "賃管試験·法令·制度分野ハブ。用語往復·週次ルート·演習15問の進め方を具体例付き解説します。",
    "exam-overview": "賃貸不動産経営管理士試験の概要。50問·120分·3分野·12,000円、初学者向けDay0と演習10問の始め方を解説します。",
    "study-plan": "賃管試験の学習計画。11/15逆算·50問計測·年度別過去問の週次枠と35/50修正ルールを具体例解説します。",
    "syllabus-how-to-read": "賃管試験の要項·シラバスの読み方。法改正年度の差分確認と3分野週次枠への落とし込みを解説します。",
}

# batch検証用: 同一見出しの重複回避
SECTION4_UNIQUE: dict[str, str] = {
    "field-law-basics": "法令·制度演習10問と解き直し記録",
    "field-limit-basics": "設備·税務演習10問と解き直し記録",
    "field-rights-basics": "契約·実務演習10問と解き直し記録",
    "insurance-property-risk": "保険·リスク演習10問と解き直し記録",
}


def main() -> None:
    rows = list(csv.DictReader((ROOT / "data/guide_articles.csv").open(encoding="utf-8-sig")))
    from tools.editorial_quality import is_published_guide

    pub = [r for r in rows if is_published_guide(r)]
    slugs = [r["slug"] for r in pub if has_s5_2col(r)]
    # affiliate with 2col not in list? include all published affiliate
    for r in pub:
        if r["slug"].startswith("affiliate-") and r["slug"] not in slugs and has_s5_2col(r):
            slugs.append(r["slug"])
    slugs = sorted(set(slugs))
    overrides: dict[str, dict] = {}
    for r in pub:
        if r["slug"] not in slugs:
            continue
        topic = topic_from_row(r)
        overrides[r["slug"]] = make_s5(topic, r["slug"])
        if r["slug"] in SECTION4_UNIQUE:
            overrides[r["slug"]]["section_4_heading"] = SECTION4_UNIQUE[r["slug"]]
        if r["slug"] in PHASE1_META:
            overrides[r["slug"]]["meta_description"] = PHASE1_META[r["slug"]]
            overrides[r["slug"]]["revision_note"] = (
                "2026-06-18: GSC着地品質リライト Phase1-2（手書きリライト・具体例）"
                if not r["slug"].startswith("affiliate-")
                else "2026-06-18: GSC着地品質リライト Phase1（アフィリエイト・具体例）"
            )

    out = ROOT / "tools" / "chintai_s5_decompare_overrides.py"
    lines = [
        '#!/usr/bin/env python3',
        '# -*- coding: utf-8 -*-',
        '"""chintaikanrishi section5差し替え（自動生成 + Phase1 meta）。"""',
        "",
        "from __future__ import annotations",
        "",
        "import re",
        "",
        "META_2COL_RE = re.compile(r\"[^。]*2列比較[^。]*。?\")",
        "",
        "",
        "def scrub_meta(text: str) -> str:",
        '    t = META_2COL_RE.sub("", text or "").strip()',
        '    if not t.endswith("。"):',
        '        t += "。"',
        "    return t",
        "",
        "",
        "def scrub_user_intent(text: str) -> str:",
        '    t = (text or "").replace("使い分けも表で把握できます", "使い分けも本文で把握できます")',
        '    t = t.replace("使い分けも表で把握", "使い分けも本文で把握")',
        "    return t",
        "",
        "",
        "OVERRIDES: dict[str, dict[str, str]] = {",
    ]
    for slug in slugs:
        o = overrides[slug]
        lines.append(f'    "{slug}": {{')
        for k, v in o.items():
            lines.append(f"        {k!r}: {v!r},")
        lines.append("    },")
    lines.append("}")
    lines.append("")
    out.write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote {out.name} slugs={len(slugs)}")


if __name__ == "__main__":
    main()
