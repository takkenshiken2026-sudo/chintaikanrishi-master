#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Upgrade all glossary detail articles to professional expert-writer quality.

Pipeline per term:
  1. glossary_craft_engine (term-specific prose, tables, append-50 priority)
  2. Professional enrichment (purpose, exam tactics, varied titles/leads)
  3. improve_glossary_readability (plain Japanese, examples, memory, FAQ×4)

Run:
  python3 tools/professional_content_upgrade.py
  python3 tools/build_glossary_pages.py
"""

from __future__ import annotations

import csv
import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.glossary_craft_engine import craft_term, craft_exam_focus  # noqa: E402
from tools.improve_glossary_readability import (  # noqa: E402
    build_faqs,
    build_memory_tip,
    build_summary_body,
    improve_row,
    norm,
    plain_text,
    split_semicolon,
    split_sentences,
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

TITLE_PATTERNS = (
    "{term}とは？試験で問われる意味とポイント",
    "【賃管試験】{term}の意味・条文・頻出の見方",
    "{term}の解説｜定義・具体例・よくある誤り",
    "{term}を試験で落とさないための整理",
)

LEAD_OPENERS = (
    "賃貸不動産経営管理士試験では、実務と法令が交差する論点として「{term}」が繰り返し問われます。",
    "「{term}」は、一見すると定義暗記で済ませがちですが、肢では条件の一部が抜けた言い換えが仕掛けられます。",
    "受験生がつまずきやすい「{term}」を、制度の目的から試験の解法まで順に整理します。",
    "本記事では「{term}」を、短い定義だけでなく、場面・条文・類似語との違いまで含めて解説します。",
)

PURPOSE_BY_CATEGORY: dict[str, str] = {
    "賃貸住宅管理業法": (
        "この制度は、管理業務の適正化と預り金の保護を目的に、"
        "登録・書面・説明義務・監督処分までを一体的に定めています。"
    ),
    "借地借家法": (
        "借地借家法は、借主の居住の安定と、貸主の権利の均衡を図るため、"
        "更新・立退・正当事由などのルールを設けています。"
    ),
    "民法": (
        "改正民法を含む民法の規定は、賃貸借の終了・損害・担保など、"
        "トラブル発生後の法的手段を整理するうえで土台になります。"
    ),
    "管理実務": (
        "現場の運用ルールは、法令の要件を満たしつつ、入居者・オーナー双方の紛争を防ぐために整備されます。"
    ),
    "原状回復": (
        "原状回復は、退去時の費用負担を公平に決めるための枠組みで、"
        "判例・民法・ガイドライン・特約の関係を押さえる必要があります。"
    ),
    "建物・設備": (
        "建物・設備に関する論点は、維持保全義務と点検・共用部分の管理が、"
        "管理業務の三要素とも結びついて出題されます。"
    ),
    "賃貸経営・PM/AM": (
        "賃貸経営の知識は、オーナーへの説明責任と、管理会社の業務範囲の説明に直結します。"
    ),
    "会計・税務・保険": (
        "会計・税務・保険は、管理報酬や修繕費、リスク対応を数値と制度の両面から理解する分野です。"
    ),
    "関連法令": (
        "賃管業法以外の法令は、物件の種類や利用形態によって適用が分かれるため、"
        "適用場面の特定が試験の焦点になります。"
    ),
    "賃貸借契約": (
        "賃貸借契約に関する制度は、説明・交付・成立の時系列を誤ると一問まるごと落としやすい領域です。"
    ),
}


def term_hash(term: str) -> int:
    return int(hashlib.md5(term.encode()).hexdigest(), 16)


def parse_numbered(defn: str) -> list[str]:
    return [p.strip().rstrip("。") for p in re.findall(r"[①②③④⑤]([^①②③④⑤]+)", defn)]


def key_clause(defn: str) -> str:
    for sent in split_sentences(defn):
        s = sent.rstrip("。")
        if any(
            k in s
            for k in ("必要", "要件", "禁止", "しない", "ない", "のみ", "併せ", "交付", "承諾", "遅滞")
        ):
            return s
    sents = split_sentences(defn)
    return sents[-1].rstrip("。") if sents else defn[:80]


def professional_title(term: str) -> str:
    return TITLE_PATTERNS[term_hash(term) % len(TITLE_PATTERNS)].format(term=term)


def professional_lead(row: dict[str, str]) -> str:
    term = row["term"].strip()
    short = plain_text(norm(row.get("short_def")).rstrip("。"))
    category = norm(row.get("category"))
    imp = norm(row.get("importance"))
    opener = LEAD_OPENERS[term_hash(term) % len(LEAD_OPENERS)].format(term=term)
    imp_note = "重要度Aの頻出語です。" if imp == "A" else ""
    return plain_text(
        f"{opener}"
        f"一言で言うと「{short}」。"
        f"{category}分野の学習では、定義に加えて根拠条文と類似語との違いまでセットで持つと得点が安定します。{imp_note}"
    )


def purpose_paragraph(row: dict[str, str]) -> str:
    cat = norm(row.get("category"))
    base = PURPOSE_BY_CATEGORY.get(
        cat,
        "試験では、制度の目的と要件を結びつけて理解しているかが問われます。",
    )
    term = row["term"].strip()
    return plain_text(f"まず制度の背景です。{base}「{term}」は、そのなかで次のように位置づけられます。")


def exam_tactics_paragraph(row: dict[str, str], exam_points: list[str]) -> str:
    term = row["term"].strip()
    if exam_points:
        first = exam_points[0].rstrip("。")
        second = exam_points[1].rstrip("。") if len(exam_points) > 1 else ""
        if second:
            return plain_text(
                f"試験では、肢を読む前に「{first}」を確認し、"
                f"次に「{second}」に合わない選択肢を除外する読み方が有効です。"
                f"正しい肢ほど、{term}の定義の一部だけを抜き出した表現になっている点に注意してください。"
            )
        return plain_text(
            f"試験では「{first}」が満たされているかを基準に判断します。"
            f"結論だけを見ず、定義文の条件語（誰が・いつ・何を）まで照合してください。"
        )
    kc = key_clause(norm(row.get("definition")))
    return plain_text(
        f"選択肢では「{kc}」の有無が分岐点になりやすいです。"
        f"用語名の印象で選ばず、定義文に当てはめてから答えを決めてください。"
    )


def enrich_detail_body(row: dict[str, str], base: str, exam_points: list[str]) -> str:
    if not base.strip():
        return base
    parts = [purpose_paragraph(row), base.strip(), exam_tactics_paragraph(row, exam_points)]
    return "\n\n".join(parts)


def professional_explanation(row: dict[str, str], exam_points: list[str]) -> str:
    term = row["term"].strip()
    short = plain_text(norm(row.get("short_def")).rstrip("。"))
    if exam_points:
        focus = exam_points[0].rstrip("。")
        return plain_text(
            f"{term}は「{short}」を中心とする用語です。"
            f"過去問形式の演習では、{focus}を基準に正誤を切り分ける練習を重ねると理解が深まります。"
        )
    return plain_text(
        f"{term}は「{short}」です。"
        f"関連用語との比較表と具体例をあわせて読み返すと、似た肢への引っかかりを減らせます。"
    )


def strip_banned(text: str) -> str:
    t = text
    for phrase in BANNED_PHRASES:
        t = t.replace(phrase, "")
    return re.sub(r"\n{3,}", "\n\n", t).strip()


def upgrade_glossary_row(row: dict[str, str], lookup: dict[str, dict[str, str]]) -> None:
    term = row["term"].strip()
    crafted = craft_term(row, lookup)

    for col in DETAIL_COLS:
        if crafted.get(col):
            row[col] = crafted[col]

    exam_points = [p.strip() for p in norm(row.get("exam_points")).split(";") if p.strip()]

    row["article_title"] = professional_title(term)
    row["article_lead"] = professional_lead(row)
    if norm(row.get("term_detail_body")):
        row["term_detail_body"] = strip_banned(
            enrich_detail_body(row, norm(row["term_detail_body"]), exam_points)
        )
    row["explanation"] = professional_explanation(row, exam_points)
    if exam_points:
        row["exam_focus"] = plain_text(craft_exam_focus(term, exam_points))
    row["common_mistakes"] = plain_text(norm(row.get("common_mistakes")))

    related = split_semicolon(row.get("related_terms") or "")
    row["summary_body"] = build_summary_body(row, related)
    row["memory_tip"] = build_memory_tip(row, related, exam_points)
    row.update(build_faqs(row, lookup, related))

    improve_row(row, lookup)
    row["article_lead"] = professional_lead(row)
    row["explanation"] = professional_explanation(row, exam_points)


def main() -> int:
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    fieldnames = list(rows[0].keys()) if rows else []
    for col in ("faq_4_question", "faq_4_answer"):
        if col not in fieldnames:
            fieldnames.append(col)

    lookup = {r["term"].strip(): r for r in rows}
    for row in rows:
        upgrade_glossary_row(row, lookup)

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    banned_hits = 0
    for r in rows:
        blob = " ".join(norm(r.get(c)) for c in DETAIL_COLS)
        if any(p in blob for p in BANNED_PHRASES):
            banned_hits += 1

    print(f"Upgraded {len(rows)} glossary terms → {CSV_PATH}")
    print(f"  banned phrase remnants: {banned_hits}/{len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
