#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upgrade all glossary detail articles to professional / expert-writer quality.

Pipeline per term:
1. glossary_craft_engine (term-specific prose from definition)
2. append_glossary_50_terms override where available
3. Pro enrichment (exam solver, practical lens, banned-phrase cleanup)
4. improve_glossary_readability (plain Japanese, examples, memory, FAQ×4)

Run: python3 tools/glossary_pro_writer.py
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.glossary_craft_engine import craft_from_append, craft_term  # noqa: E402
from tools.improve_glossary_readability import (  # noqa: E402
    build_faqs,
    build_memory_tip,
    build_summary_body,
    improve_row,
    norm,
    plain_text,
    split_semicolon,
    simplify_body,
    simplify_lead,
)
from tools.upgrade_glossary_quality import BANNED_PHRASES  # noqa: E402

CSV_PATH = ROOT / "data" / "glossary_terms.csv"

DETAIL_COLS = [
    "article_title",
    "article_lead",
    "term_detail_body",
    "exam_points",
    "common_mistakes",
    "memory_tip",
    "example_question",
    "example_answer",
    "faq_1_question",
    "faq_1_answer",
    "faq_2_question",
    "faq_2_answer",
    "faq_3_question",
    "faq_3_answer",
    "faq_4_question",
    "faq_4_answer",
    "summary_body",
    "comparison_table",
    "exam_focus",
    "explanation",
]

CATEGORY_PRACTICAL: dict[str, str] = {
    "賃貸住宅管理業法": (
        "実務では、登録・書面交付・預り金の分別管理がセットで問われます。"
        "オーナー・入居者・管理会社のどの立場の義務かを先に固定してから条文を当てはめてください。"
    ),
    "借地借家法": (
        "実務・試験ともに「更新するか／期間満了で終わるか」の軸が最重要です。"
        "通知の時期・方法・正当事由の有無を、用語ごとに一言で言えるようにしておきましょう。"
    ),
    "民法": (
        "賃料滞納・解除・損害賠償など、トラブル発生後の救済手段として出題されます。"
        "条文の要件（催告の要否、期間、効果）を、場面イメージと結びつけると得点しやすくなります。"
    ),
    "管理実務": (
        "現場では書面・記録・説明責任が争点になりやすい論点が多いです。"
        "口頭だけで済ませない手続（明細書、重説、締結時書面）と対応づけて覚えてください。"
    ),
    "原状回復": (
        "退去精算では、通常損耗・経年変化と借主負担の線引きが中心です。"
        "ガイドラインは実務指針であり、契約特約・判例と併せて判断する点が試験でも問われます。"
    ),
    "建物・設備": (
        "維持保全・点検・共用部分の管理は、管理業務の三要素と結びつきます。"
        "誰が点検し、記録を残し、修繕費を負担するかをセットで整理してください。"
    ),
    "賃貸経営・PM/AM": (
        "家賃収入・空室・修繕費・税務のバランスが経営判断の軸です。"
        "用語が「収益」「コスト」「リスク」のどれに関わるかを意識すると理解が早くなります。"
    ),
    "会計・税務・保険": (
        "数値・期限・控除の有無は年度で変わりうるため、本番前に公式情報を確認してください。"
        "制度の目的（課税関係の整理、リスク移転）を押さえると暗記が楽になります。"
    ),
    "関連法令": (
        "賃管業法以外の法令（消防・区分所有・民泊等）と役割分担が問われます。"
        "義務主体が管理会社か、オーナーか、入居者かを明確にしてください。"
    ),
    "賃貸借契約": (
        "仲介・重説・契約書・入居後のトラブルまで、時系列で用語を並べると混乱しにくくなります。"
        "宅建業法と賃管業法の書面は、交付時期が異なる点に特に注意してください。"
    ),
}

TITLE_VARIANTS = (
    "{term}とは？試験で押さえる意味と使い方",
    "{term}の意味と試験ポイント｜定義・根拠・関連語",
    "【賃管試験】{term}を理解する｜定義と頻出の落とし穴",
)


def term_hash(term: str) -> int:
    import hashlib

    return int(hashlib.md5(term.encode()).hexdigest(), 16)


def clean_exam_points(points: list[str]) -> list[str]:
    junk_fragments = (
        "定義語句（主体・要件・効果）",
        "そのまま再現できるようにする",
        "1分で説明できるようにする",
        "誤った言い換え肢を除外",
    )
    out: list[str] = []
    seen: set[str] = set()
    for p in points:
        p = plain_text(p.strip().rstrip("。"))
        if not p or any(j in p for j in junk_fragments):
            continue
        key = p[:36]
        if key in seen:
            continue
        seen.add(key)
        out.append(p + "。")
    return out[:4]


def clean_text_field(text: str) -> str:
    t = plain_text(text)
    for banned in BANNED_PHRASES:
        if banned in t:
            t = t.replace(banned, "")
    t = re.sub(r"\n{3,}", "\n\n", t)
    return t.strip()


def pro_exam_focus(term: str, exam_points: list[str], related: list[str]) -> str:
    if len(exam_points) >= 2:
        return (
            f"「{term}」の問題では、まず「{exam_points[0].rstrip('。')}」に当てはまる肢を残し、"
            f"次に「{exam_points[1].rstrip('。')}」と矛盾する肢を除外する読み方が有効です。"
        )
    if exam_points:
        return (
            f"「{term}」では、「{exam_points[0].rstrip('。')}」を基準に、"
            f"定義の主語・時期・効果がずれた肢を先に落としてください。"
        )
    if related:
        return (
            f"「{term}」と「{related[0]}」の違い（いつ・誰が・何が起きるか）を"
            f"一言で言えるかが、類似肢対策の要点です。"
        )
    return f"「{term}」は、定義文の限定語（のみ・併せて・ない）まで確認すると安定します。"


def enrich_detail_body(row: dict[str, str], body: str, related: list[str]) -> str:
    term = row["term"].strip()
    category = norm(row.get("category"))
    body = clean_text_field(body)
    if not body:
        return body

    exam_para = (
        f"試験では、{term}の選択肢を読むときは、定義の「主語（誰）」「時期（いつ）」「効果（何が起きる）」"
        f"の3点に印をつけてから肢を見ると、言い換えの陷阱に引っかかりにくくなります。"
    )
    practical = CATEGORY_PRACTICAL.get(
        category,
        "場面（契約前・入居中・退去時）を一つ想像し、そのとき誰の義務・権利かを確認してから条文を当てはめてください。",
    )

    parts = [p for p in re.split(r"\n{2,}", body) if p.strip()]
    if exam_para not in body:
        parts.append(exam_para)
    if practical not in body and len(parts) < 5:
        parts.append(practical)

    if related and related[0] not in body:
        parts.append(
            f"関連用語の「{related[0]}」と混同しやすいので、"
            f"両方の定義を並べて「違う一文」をメモしておくと復習効率が上がります。"
        )

    return "\n\n".join(parts)


def pro_lead(row: dict[str, str], crafted_lead: str) -> str:
    term = row["term"].strip()
    short = plain_text(norm(row.get("short_def")).rstrip("。"))
    category = norm(row.get("category"))
    imp = norm(row.get("importance"))

    cleaned = simplify_lead(crafted_lead, term, norm(row.get("short_def")), category)
    if len(cleaned) >= 80 and "頻出です。定義を暗記" not in cleaned:
        return cleaned

    imp_note = "出題頻度が高い用語です。" if imp == "A" else "押さえておきたい用語です。"
    return (
        f"「{term}」は、{short}という意味です。"
        f"{category}の論点として{imp_note}"
        f"意味だけでなく、根拠条文と関連語との違いまでセットで整理します。"
    )


def upgrade_term(row: dict[str, str], lookup: dict[str, dict[str, str]]) -> None:
    term = row["term"].strip()
    related = split_semicolon(row.get("related_terms") or "")

    crafted = craft_from_append(row) or craft_term(row, lookup)
    for col in DETAIL_COLS:
        if crafted.get(col):
            row[col] = crafted[col]

    row["article_title"] = TITLE_VARIANTS[term_hash(term) % len(TITLE_VARIANTS)].format(term=term)
    row["article_lead"] = pro_lead(row, norm(row.get("article_lead")))

    exam_points = clean_exam_points(
        [p.strip() for p in norm(row.get("exam_points")).split(";") if p.strip()]
    )
    if exam_points:
        row["exam_points"] = ";".join(exam_points)

    detail = enrich_detail_body(row, norm(row.get("term_detail_body")), related)
    row["term_detail_body"] = simplify_body(detail, term)

    row["exam_focus"] = pro_exam_focus(term, exam_points, related)
    row["common_mistakes"] = clean_text_field(
        norm(row.get("common_mistakes"))
        or f"「{term}」では、用語名の印象だけで判断し、要件の一部を読み飛ばす誤りが典型です。"
    )

    row["summary_body"] = build_summary_body(row, related)
    row["memory_tip"] = build_memory_tip(row, related, exam_points)
    row.update(build_faqs(row, lookup, related))

    row["explanation"] = plain_text(
        f"{term}は、{norm(row.get('short_def')).rstrip('。')}。"
        f"試験では場面を想像しながら定義と根拠を確認すると得点しやすくなります。"
    )


def main() -> int:
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    fieldnames = list(rows[0].keys()) if rows else []
    for col in ("faq_4_question", "faq_4_answer"):
        if col not in fieldnames:
            fieldnames.append(col)

    lookup = {r["term"].strip(): r for r in rows}
    for row in rows:
        upgrade_term(row, lookup)

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    banned_hits = 0
    for r in rows:
        blob = " ".join(norm(r.get(c)) for c in DETAIL_COLS)
        if any(b in blob for b in BANNED_PHRASES):
            banned_hits += 1

    faq4 = sum(1 for r in rows if norm(r.get("faq_4_answer")))
    print(f"Pro-upgraded {len(rows)} glossary terms in {CSV_PATH}")
    print(f"  faq_4 filled: {faq4}/{len(rows)}")
    print(f"  banned phrase rows remaining: {banned_hits}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
