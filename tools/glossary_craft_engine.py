#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate hand-written-quality glossary article fields from CSV source rows."""

from __future__ import annotations

import hashlib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.upgrade_glossary_quality import (  # noqa: E402
    COMPARE_TABLES,
    EXAMPLES,
    meaningful_compare_table,
)

# Reuse append_glossary curated rows when available
def _load_append_rows() -> dict[str, dict[str, str]]:
    try:
        from tools.append_glossary_50_terms import NEW_TERMS
    except ImportError:
        return {}
    return {r["term"].strip(): r for r in NEW_TERMS}


APPEND_ROWS = _load_append_rows()

LEAD_STYLES = (
    lambda t, s, c, imp: (
        f"{s.rstrip('。')}。"
        f"{t}は{c}の出題で、定義の言い換えだけでなく、条文・要件まで結びつけて覚えると得点しやすくなります。"
    ),
    lambda t, s, c, imp: (
        f"「{t}」は、{s.rstrip('。')}。"
        f"肢では文言の印象に流されず、{c}分野の制度の中での役割を確認してから選んでください。"
    ),
    lambda t, s, c, imp: (
        f"{c}分野の用語「{t}」。{s.rstrip('。')}。"
        f"関連する制度と並べて整理すると、似た選択肢の排除が速くなります。"
    ),
    lambda t, s, c, imp: (
        f"{s.rstrip('。')}点を押さえたうえで、{t}がどの手続・義務に関わるかを意識して読み進めてください。"
    ),
    lambda t, s, c, imp: (
        f"試験では「{t}」が単独で問われることも、関連制度とセットで問われることもあります。"
        f"まずは{s.rstrip('。')}という整理から始めましょう。"
    ),
    lambda t, s, c, imp: (
        f"{t}を理解するカギは、{s.rstrip('。')}という定義に加え、"
        f"根拠条文と適用場面をセットで持つことです。"
    ),
)


def norm(s: str | None) -> str:
    return (s or "").strip()


def split_semicolon(s: str) -> list[str]:
    return [x.strip() for x in (s or "").split(";") if x.strip()]


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    return [p.strip() for p in re.findall(r"[^。！？]+[。！？]?", text) if p.strip()]


def term_hash(term: str) -> int:
    return int(hashlib.md5(term.encode()).hexdigest(), 16)


def parse_numbered_clauses(defn: str) -> list[str]:
    parts = re.findall(r"[①②③④⑤⑥⑦⑧⑨⑩]([^①②③④⑤⑥⑦⑧⑨⑩]+)", defn)
    return [p.strip().rstrip("。") for p in parts if p.strip()]


def extract_list_tail(defn: str) -> list[str]:
    m = re.search(r"([^。]+(?:等)?が含まれる|等を含む|等が含まれる)[。]?", defn)
    if not m:
        return []
    chunk = m.group(1)
    items = re.split(r"[、,]", chunk.replace("等が含まれる", "").replace("が含まれる", ""))
    return [i.strip() for i in items if i.strip() and len(i.strip()) > 2][:6]


def key_clause(defn: str) -> str:
    for sent in split_sentences(defn):
        if any(k in sent for k in ("必要", "要件", "禁止", "してはならない", "ない", "のみ", "併せ", "交付", "承諾")):
            return sent.rstrip("。")
    sents = split_sentences(defn)
    return sents[-1].rstrip("。") if sents else defn[:80]


def craft_exam_points(row: dict[str, str], related: list[str], numbered: list[str]) -> list[str]:
    term = row["term"].strip()
    defn = norm(row.get("definition"))
    legal = split_semicolon(norm(row.get("legal_basis")))
    points: list[str] = []

    for item in numbered[:2]:
        points.append(item + "。")

    for sent in split_sentences(defn):
        s = sent.rstrip("。")
        if len(s) < 14 or len(s) > 85:
            continue
        if any(k in s for k in ("必要", "要件", "禁止", "しない", "ない", "のみ", "併せ", "交付", "承諾", "遅滞")):
            if s + "。" not in points:
                points.append(s + "。")
        if len(points) >= 3:
            break

    if legal and legal[0] != "—":
        points.append(f"{legal[0]}の条文と要件・効果を対応づける")

    if related and related[0] not in term:
        points.append(f"「{related[0]}」との違い（定義・手続・主体）を説明できるようにする")

    if len(points) < 3:
        short = norm(row.get("short_def")).rstrip("。")
        points.append(f"{short}という定義を、選択肢の文言と照合できる")

    seen: set[str] = set()
    out: list[str] = []
    for p in points:
        k = p[:40]
        if k not in seen:
            seen.add(k)
            out.append(p)
    return out[:4]


def craft_detail_body(row: dict[str, str], lookup: dict[str, dict[str, str]], related: list[str]) -> str:
    term = row["term"].strip()
    defn = norm(row.get("definition"))
    short = norm(row.get("short_def")).rstrip("。")
    legal = split_semicolon(norm(row.get("legal_basis")))
    numbered = parse_numbered_clauses(defn)
    paragraphs: list[str] = []

    if numbered:
        paragraphs.append(f"{term}は、{short}。")
        bullets = "。".join(f"（{i+1}）{c}" for i, c in enumerate(numbered))
        paragraphs.append(f"制度の内容は、{bullets}。試験では、この構成を崩した肢（一部だけ正しい、セット要件を無視する等）に注意してください。")
    else:
        sents = split_sentences(defn)
        paragraphs.append(defn if defn else f"{term}は、{short}。")
        if len(sents) >= 2:
            focus = key_clause(defn)
            paragraphs.append(
                f"特に「{focus}」は出題の焦点になりやすいです。"
                f"定義文の後半に書かれた条件・効果を読み飛ばさないでください。"
            )

    listed = extract_list_tail(defn)
    if listed and not numbered:
        paragraphs.append(
            f"具体的な例として、{'・'.join(listed[:5])}などが挙げられます。"
            f"これらは総称として覚えるより、{term}の文脈で何を問われるかを結びつけるとよいです。"
        )

    if legal and legal[0] != "—":
        law_txt = "・".join(legal[:3])
        paragraphs.append(f"根拠は主に{law_txt}です。条文番号と定義のキーワードを対応づけて暗記してください。")

    if related:
        rel = related[0]
        rel_row = lookup.get(rel)
        if rel_row:
            rel_short = norm(rel_row.get("short_def")).rstrip("。")
            rel_key = key_clause(norm(rel_row.get("definition")))
            paragraphs.append(
                f"「{rel}」とセットで問われることが多いです。"
                f"{rel}は{rel_short}。"
                f"一方、{term}では{key_clause(defn)}点が異なります（{rel}側は{rel_key}）。"
            )

    return "\n\n".join(paragraphs)


def craft_mistakes(row: dict[str, str], related: list[str], numbered: list[str]) -> str:
    term = row["term"].strip()
    defn = norm(row.get("definition"))

    if "無効" in defn:
        core = "有効・適法と読める肢に引っ張られる"
    elif "契約締結前" in defn or "契約前" in defn:
        core = "契約成立時の手続と取り違える"
    elif "成立時" in defn:
        core = "契約前の説明・交付と取り違える"
    elif numbered and any("のみ" in n or "ない" in n for n in numbered):
        core = "一部の要素だけで制度の要件を満たすと判断する"
    elif "ガイドライン" in term or "ガイドライン" in defn:
        core = "実務指針を法律と同一視する"
    elif "登録" in defn and ("ない" in defn or "禁止" in defn):
        core = "登録・届出が不要だとする"
    elif related:
        core = f"「{related[0]}」と同じ手続・効果だとする"
    else:
        core = "用語の意味だけ覚え、要件・効果まで確認しない"

    return (
        f"「{term}」では、{core}誤りが典型です。"
        f"肢の結論を急ぐ前に、定義文と根拠条文に当てはめてください。"
    )


def craft_memory(row: dict[str, str], related: list[str], numbered: list[str]) -> str:
    term = row["term"].strip()
    defn = norm(row.get("definition"))
    legal = split_semicolon(norm(row.get("legal_basis")))
    hooks: list[str] = []

    if numbered:
        hooks.append(f"{len(numbered)}要素")
    nums = re.findall(r"\d+[%％ヵ月年戸日条]", defn)
    hooks.extend(nums[:2])
    if legal and legal[0] != "—":
        hooks.append(legal[0])
    if related:
        hooks.append(f"≠{related[0]}")
    if not hooks:
        hooks.append(key_clause(defn)[:20])

    return f"{term}：{'／'.join(hooks[:4])}"


def craft_faqs(row: dict[str, str], lookup: dict[str, dict[str, str]], related: list[str]) -> dict[str, str]:
    term = row["term"].strip()
    defn = norm(row.get("definition"))
    short = norm(row.get("short_def"))
    legal = split_semicolon(norm(row.get("legal_basis")))
    numbered = parse_numbered_clauses(defn)

    faq1_a = split_sentences(defn)[0] if split_sentences(defn) else f"{term}とは、{short.rstrip('。')}。"

    if related and related[0] in lookup:
        rel = related[0]
        rel_def = norm(lookup[rel].get("definition"))
        faq2_q = f"{term}と{rel}の違いは何ですか？"
        faq2_a = (
            f"{term}は{key_clause(defn)}。"
            f"{rel}は{key_clause(rel_def)}。"
            f"試験では、両者の定義文で異なる語句（主体・時期・効果）を確認してください。"
        )
    elif numbered:
        faq2_q = f"{term}の構成要素は何ですか？"
        faq2_a = "。".join(f"（{i+1}）{c}" for i, c in enumerate(numbered)) + "。"
    else:
        faq2_q = f"{term}で試験では何を問われますか？"
        faq2_a = f"定義のうち「{key_clause(defn)}」が満たされるか、関連制度と混同しないかが中心です。"

    if legal and legal[0] != "—":
        faq3_q = f"{term}の根拠法令は何ですか？"
        faq3_a = f"主な根拠は{'・'.join(legal[:3])}です。条文の要件と定義を対応づけて覚えてください。"
    else:
        faq3_q = f"{term}を覚えるときのコツは？"
        faq3_a = craft_memory(row, related, numbered)

    return {
        "faq_1_question": f"{term}とは何ですか？",
        "faq_1_answer": faq1_a,
        "faq_2_question": faq2_q,
        "faq_2_answer": faq2_a,
        "faq_3_question": faq3_q,
        "faq_3_answer": faq3_a,
    }


def craft_summary(row: dict[str, str], numbered: list[str]) -> str:
    term = row["term"].strip()
    short = norm(row.get("short_def")).rstrip("。")
    imp = norm(row.get("importance"))
    extra = ""
    if numbered:
        extra = f"制度は{len(numbered)}つの要素で理解します。"
    elif key_clause(norm(row.get("definition"))) != short:
        extra = f"{key_clause(norm(row.get('definition')))}。"
    imp_note = "出題頻度が高い用語です。" if imp == "A" else ""
    return f"{short}。{extra}{imp_note}".strip()


def craft_exam_focus(term: str, exam_points: list[str]) -> str:
    if len(exam_points) >= 2:
        return (
            f"「{term}」の問題では、まず「{exam_points[0].rstrip('。')}」を確認し、"
            f"次に「{exam_points[1].rstrip('。')}」に合わない肢を除外する読み方が有効です。"
        )
    if exam_points:
        return f"「{term}」では、「{exam_points[0].rstrip('。')}」を基準に定義と矛盾する肢を除外してください。"
    return ""


def craft_from_append(row: dict[str, str]) -> dict[str, str] | None:
    term = row["term"].strip()
    base = APPEND_ROWS.get(term)
    if not base:
        return None
    out = {k: v for k, v in base.items() if v and k not in ("term", "reading", "category", "tags", "short_def", "definition", "related_terms", "legal_basis", "importance")}
    if not out.get("faq_3_question"):
        faqs = craft_faqs(row, {}, split_semicolon(row.get("related_terms") or ""))
        out.setdefault("faq_3_question", faqs["faq_3_question"])
        out.setdefault("faq_3_answer", faqs["faq_3_answer"])
    if not out.get("summary_body"):
        out["summary_body"] = craft_summary(row, parse_numbered_clauses(norm(row.get("definition"))))
    if not out.get("exam_focus") and out.get("exam_points"):
        pts = [p.strip() for p in out["exam_points"].split(";") if p.strip()]
        out["exam_focus"] = craft_exam_focus(term, pts)
    table = COMPARE_TABLES.get(term) or meaningful_compare_table(term, row, split_semicolon(row.get("related_terms") or ""), {row["term"]: row})
    if table and not out.get("comparison_table"):
        out["comparison_table"] = table
    return out


def craft_term(row: dict[str, str], lookup: dict[str, dict[str, str]]) -> dict[str, str]:
    appended = craft_from_append(row)
    if appended:
        return appended

    term = row["term"].strip()
    category = norm(row.get("category"))
    short = norm(row.get("short_def"))
    related = split_semicolon(row.get("related_terms") or "")
    defn = norm(row.get("definition"))
    numbered = parse_numbered_clauses(defn)
    exam_points = craft_exam_points(row, related, numbered)
    pts_join = ";".join(exam_points)

    h = term_hash(term) % len(LEAD_STYLES)
    article_lead = LEAD_STYLES[h](term, short, category, norm(row.get("importance")))

    faqs = craft_faqs(row, lookup, related)
    payload: dict[str, str] = {
        "article_title": f"{term}とは？意味・試験ポイントを整理",
        "article_lead": article_lead,
        "term_detail_body": craft_detail_body(row, lookup, related),
        "exam_points": pts_join,
        "exam_focus": craft_exam_focus(term, exam_points),
        "summary_body": craft_summary(row, numbered),
        "common_mistakes": craft_mistakes(row, related, numbered),
        "memory_tip": craft_memory(row, related, numbered),
        "explanation": (
            f"{term}は、{short.rstrip('。')}。"
            f"試験では{exam_points[0].rstrip('。') if exam_points else '定義と要件'}が問われやすいです。"
        ),
        **faqs,
    }

    table = COMPARE_TABLES.get(term)
    if not table:
        table = meaningful_compare_table(term, row, related, lookup)
    if table:
        payload["comparison_table"] = table

    imp = norm(row.get("importance"))
    if imp == "A" and term in EXAMPLES:
        q, a = EXAMPLES[term]
        payload["example_question"] = q
        payload["example_answer"] = a

    return payload


def craft_all(rows: list[dict[str, str]]) -> dict[str, dict[str, str]]:
    lookup = {r["term"].strip(): r for r in rows}
    return {r["term"].strip(): craft_term(r, lookup) for r in rows}
