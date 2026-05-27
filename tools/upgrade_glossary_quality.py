#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Upgrade glossary detail articles with term-specific content derived from definitions.

- Hand-crafted rows from append_glossary_50_terms.py are preserved.
- Other rows: no category boilerplate; prose is built from each term's definition,
  legal_basis, tags, and related-term contrasts.
"""

from __future__ import annotations

import argparse
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CSV_PATH = ROOT / "data" / "glossary_terms.csv"

# Phrases that indicate low-originality template content (should be near zero after upgrade)
BANNED_PHRASES = (
    "主体・時期・承諾・数値",
    "過去問では、",
    "それぞれの制度の目的と要件の差を一言で言えると得点",
    "選択肢では「",
    "名称だけに反応して結論を急ぐ",
    "賃貸住宅管理業法は、管理業務の適正化と預り金の保護が目的です。",
    "借地借家法は借主保護が中心です。",
    "試験では定義・交付時期・主体・数値の有無を表にまとめ",
)

COMPARE_TABLES: dict[str, str] = {
    "締結時書面": """<table class="seo-info-table"><thead><tr><th>書面</th><th>交付時期</th><th>主な根拠</th></tr></thead><tbody>
<tr><th>重要事項説明書</th><td>契約締結前</td><td>宅建35条／賃管13・30条</td></tr>
<tr><th>締結時書面</th><td>契約成立時</td><td>賃管14条／31条</td></tr>
<tr><th>37条書面</th><td>契約成立時</td><td>宅建37条</td></tr>
</tbody></table>""",
    "35条書面": """<table class="seo-info-table"><thead><tr><th>書面</th><th>時期</th><th>説明者</th></tr></thead><tbody>
<tr><th>35条書面（重説）</th><td>契約前</td><td>宅建士</td></tr>
<tr><th>37条書面</th><td>成立時</td><td>宅建士記名</td></tr>
<tr><th>締結時書面</th><td>成立時</td><td>賃管業法の契約書</td></tr>
</tbody></table>""",
    "定期借家": """<table class="seo-info-table"><thead><tr><th>項目</th><th>定期借家</th><th>普通借家</th></tr></thead><tbody>
<tr><th>更新</th><td>原則なし</td><td>法定更新あり</td></tr>
<tr><th>事前説明</th><td>独立書面が必要</td><td>38条の制度は別</td></tr>
<tr><th>終了</th><td>終了通知が中心</td><td>更新拒絶通知</td></tr>
</tbody></table>""",
    "普通借家": """<table class="seo-info-table"><thead><tr><th>項目</th><th>普通借家</th><th>定期借家</th></tr></thead><tbody>
<tr><th>更新</th><td>原則更新（正当事由で拒絶可）</td><td>更新なし</td></tr>
<tr><th>1年未満</th><td>期間の定めなしとみなす</td><td>38条の要件</td></tr>
</tbody></table>""",
    "IT重説": """<table class="seo-info-table"><thead><tr><th>要件</th><th>内容</th></tr></thead><tbody>
<tr><th>双方向性</th><td>映像・音声で質疑応答</td></tr>
<tr><th>事前書面交付</th><td>説明前に書面交付</td></tr>
<tr><th>承諾</th><td>相手方の同意</td></tr>
</tbody></table>""",
    "基幹業務": """<table class="seo-info-table"><thead><tr><th>要素</th><th>単独</th><th>管理業務</th></tr></thead><tbody>
<tr><th>維持保全</th><td>該当せず</td><td rowspan="3">三者セットで該当</td></tr>
<tr><th>金銭管理</th><td>該当せず</td></tr>
<tr><th>基幹業務</th><td>該当せず</td></tr>
</tbody></table>""",
    "原状回復ガイドライン": """<table class="seo-info-table"><thead><tr><th>区分</th><th>負担（原則）</th></tr></thead><tbody>
<tr><th>通常損耗・経年変化</th><td>貸主</td></tr>
<tr><th>故意・過失</th><td>借主</td></tr>
</tbody></table>""",
    "更新拒絶通知": """<table class="seo-info-table"><thead><tr><th></th><th>普通借家</th><th>定期借家</th></tr></thead><tbody>
<tr><th>更新</th><td>拒絶通知</td><td>なし</td></tr>
<tr><th>終了</th><td>満了＋拒絶</td><td>終了通知</td></tr>
</tbody></table>""",
}
COMPARE_TABLES["金銭管理"] = COMPARE_TABLES["基幹業務"]
COMPARE_TABLES["管理業務"] = COMPARE_TABLES["基幹業務"]
COMPARE_TABLES["定期建物賃貸借契約"] = COMPARE_TABLES["定期借家"]
COMPARE_TABLES["重要事項説明（宅建業法）"] = COMPARE_TABLES["35条書面"]

EXAMPLES: dict[str, tuple[str, str]] = {
    "IT重説": ("事前書面交付なしでIT重説のみ実施した。適法か。", "×。事前書面交付と相手方の承諾が必要。"),
    "締結時書面": ("管理受託契約成立後に締結時書面を交付した。適切か。", "×。成立時に遅滞なく交付（賃管14条）。"),
    "基幹業務": ("維持保全と金銭管理のみ受託。管理業務か。", "×。基幹業務も併せて行う場合に管理業務。"),
    "定期借家": ("定期借家満了前に更新拒絶通知を出した。適切か。", "×。定期は更新がなく終了通知が論点。"),
    "無登録営業": ("250戸を登録なく管理。適法か。", "×。200戸以上は登録必須。"),
    "二重賃貸借": ("同一部屋に後から別の借主と契約。先の借主は。", "先の賃借権・引渡しを有する者が優先しうる。"),
    "建物明渡請求": ("賃料滞納のみで明渡しを求めた。認められるか。", "×。賃貸借終了後に明渡しを求める。"),
    "借主負担特約": ("経年変化も借主負担特約のみ。有効か。", "×。通常損耗・経年変化は貸主負担が原則。"),
    "更新料": ("更新料を家賃2ヵ月分請求。適法か。", "×。原則1ヵ月分を超えない。"),
}

REQUIREMENT_MARKERS = (
    "必要", "要件", "しなければ", "できない", "してはならない", "禁止",
    "のみ", "併せ", "承諾", "交付", "登録", "無効", "義務", "遅滞なく",
)
TIMING_MARKERS = ("契約前", "契約締結前", "成立時", "満了", "日前", "ヵ月前", "年前", "以内", "以上")
CONTRAST_MARKERS = ("一方", "に対し", "とは異な", "区別", "別途", "単独")


def norm(s: str | None) -> str:
    return (s or "").strip()


def split_semicolon(s: str) -> list[str]:
    return [x.strip() for x in (s or "").split(";") if x.strip()]


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    return [p.strip() for p in re.findall(r"[^。！？]+[。！？]?", text) if p.strip()]


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def load_handcrafted_overrides() -> dict[str, dict[str, str]]:
    """Rows authored in append_glossary_50_terms.py (high originality)."""
    try:
        from tools.append_glossary_50_terms import NEW_TERMS
    except ImportError:
        return {}
    out: dict[str, dict[str, str]] = {}
    for row in NEW_TERMS:
        term = row["term"].strip()
        out[term] = {k: v for k, v in row.items() if v}
    return out


def score_sentence(s: str) -> int:
    score = 0
    for m in REQUIREMENT_MARKERS + TIMING_MARKERS:
        if m in s:
            score += 3
    if re.search(r"\d+", s):
        score += 2
    if "条" in s:
        score += 2
    if len(s) > 25:
        score += 1
    return score


def pick_study_sentences(defn: str, limit: int = 2) -> list[str]:
    sents = split_sentences(defn)
    ranked = sorted(sents, key=score_sentence, reverse=True)
    picked: list[str] = []
    seen: set[str] = set()
    for s in ranked:
        key = s[:50]
        if key in seen:
            continue
        seen.add(key)
        picked.append(s)
        if len(picked) >= limit:
            break
    return picked or sents[:1]


def shorten_clause(text: str, max_len: int = 72) -> str:
    t = text.rstrip("。")
    if len(t) <= max_len:
        return t
    cut = t[:max_len]
    if "、" in cut:
        return cut.rsplit("、", 1)[0]
    return cut + "…"


def derive_exam_points(row: dict[str, str], related: list[str]) -> list[str]:
    term = row["term"].strip()
    defn = norm(row.get("definition"))
    legal = norm(row.get("legal_basis"))
    points: list[str] = []

    for sent in pick_study_sentences(defn, limit=3):
        s = shorten_clause(sent.rstrip("。"))
        if len(s) < 12:
            continue
        if s.startswith(term) and len(s) < 28:
            continue
        points.append(s + "。")

    for law in split_semicolon(legal):
        if law and law != "—":
            points.append(f"根拠（{law}）の要件・効果を条文とセットで押さえる")

    if related and related[0] in {term}:
        related = related[1:]
    if related:
        points.append(f"「{related[0]}」との違い（定義・手続・効果）を説明できるようにする")

    tags = split_semicolon(row.get("tags") or "")
    for tag in tags[:1]:
        if tag and tag not in term and len(tag) > 1:
            points.append(f"「{tag}」に関する設問と結びつけて復習する")

    seen: set[str] = set()
    unique: list[str] = []
    for p in points:
        k = p[:45]
        if k not in seen:
            seen.add(k)
            unique.append(p)
    return unique[:4] if unique else [f"{term}の定義と、法令上の位置づけを説明できるようにする"]


def expand_study_angle(term: str, sentence: str) -> str:
    s = sentence.rstrip("。")
    if any(m in s for m in ("必要", "要件", "しなければ", "義務")):
        if s.endswith("要件") or "が要件" in s:
            return f"試験では、{s}が満たされているかを確認する設問が出やすいです。"
        return f"試験では、{s}という点が要件として問われやすいです。"
    if any(m in s for m in ("できない", "禁止", "してはならない", "無効")):
        return f"肢の中に、{s}に反する行為を適法・有効とする記述がないか確認してください。"
    if any(m in s for m in TIMING_MARKERS):
        return f"時期の問題では、{s}という時点を、重説・契約書・通知など他の手続と取り違えないようにしてください。"
    return f"{s}が、この用語の理解の中心になります。"


def build_term_detail_body(
    row: dict[str, str],
    related: list[str],
    lookup: dict[str, dict[str, str]],
) -> str:
    term = row["term"].strip()
    defn = norm(row.get("definition"))
    paragraphs = [defn] if defn else []
    used_sents: set[str] = set()
    expand_limit = 1 if len(split_sentences(defn)) <= 2 else 2

    for sent in pick_study_sentences(defn, limit=expand_limit):
        key = sent[:60]
        if key in used_sents:
            continue
        used_sents.add(key)
        paragraphs.append(expand_study_angle(term, sent))

    if related:
        rel = related[0]
        rel_row = lookup.get(rel)
        if rel_row:
            rel_def = norm(rel_row.get("definition")) or norm(rel_row.get("short_def"))
            rel_hook = pick_study_sentences(rel_def, limit=1)
            rel_line = rel_hook[0].rstrip("。") if rel_hook else norm(rel_row.get("short_def")).rstrip("。")
            paragraphs.append(
                f"関連する「{rel}」は、{rel_line}。"
                f"「{term}」と比較するときは、両者の定義文で異なる要件・効果の語句に注目してください。"
            )

    return "\n\n".join(p for p in paragraphs if p)


def detect_mistake_pattern(defn: str, term: str, related: list[str]) -> str:
    if "無効" in defn:
        return "有効・適法であるかのように読む肢"
    if "契約締結前" in defn or "契約前" in defn:
        return "契約成立時の手続と取り違える肢"
    if "契約成立" in defn or "成立時" in defn:
        return "契約前の説明・交付と取り違える肢"
    if "のみ" in defn and ("併せ" in defn or "セット" in defn or "加え" in defn):
        return "一部の業務だけで要件を満たすとする肢"
    if "ガイドライン" in term or "ガイドライン" in defn:
        return "ガイドラインを法律そのものと同一視する肢"
    if "更新" in defn and "定期" in term:
        return "法定更新があるとする肢"
    if related:
        return f"「{related[0]}」と同一の制度・手続だとする肢"
    if "登録" in defn and "無" in defn:
        return "登録がなくても適法だとする肢"
    return "定義語だけにとらえ、要件・効果まで読まない肢"


def build_common_mistakes(row: dict[str, str], related: list[str]) -> str:
    term = row["term"].strip()
    defn = norm(row.get("definition"))
    pattern = detect_mistake_pattern(defn, term, related)
    rel_bit = ""
    if related:
        rel_bit = f"「{related[0]}」との混同も多いため、両者の定義文を並べて差分を確認してください。"
    return (
        f"「{term}」では、{pattern}に引っ張られやすいです。"
        f"{rel_bit}"
        f"正誤は、定義文と根拠条文に照らして判断してください。"
    ).strip()


def build_memory_tip(row: dict[str, str], related: list[str]) -> str:
    term = row["term"].strip()
    defn = norm(row.get("definition"))
    legal = norm(row.get("legal_basis"))
    nums = re.findall(r"\d+[%％ヵ月年戸条]", defn)
    hooks: list[str] = []
    if nums:
        hooks.append("・".join(nums[:3]))
    for m in TIMING_MARKERS:
        if m in defn:
            hooks.append(m)
            break
    laws = split_semicolon(legal)
    if laws and laws[0] != "—":
        hooks.append(laws[0])
    if related:
        hooks.append(f"⇔{related[0]}")
    if not hooks:
        sents = pick_study_sentences(defn, 1)
        if sents:
            hooks.append(sents[0][:28].rstrip("。"))
    return f"{term}：{'／'.join(hooks[:4])}"


def build_article_lead(row: dict[str, str]) -> str:
    term = row["term"].strip()
    short = norm(row.get("short_def")).rstrip("。")
    study = pick_study_sentences(norm(row.get("definition")), 1)
    hook = study[0].rstrip("。") if study else short
    if hook == short:
        return f"{short}。{term}の意味と、試験で問われやすい要件を整理します。"
    return f"{short}。とくに{hook}という点が、{term}を理解するうえでの焦点です。"


def build_summary_body(row: dict[str, str]) -> str:
    term = row["term"].strip()
    short = norm(row.get("short_def")).rstrip("。")
    study = pick_study_sentences(norm(row.get("definition")), 1)
    extra = study[0] if study and study[0].rstrip("。") != short else ""
    imp = norm(row.get("importance"))
    imp_note = "本試験では特に出題頻度が高い用語です。" if imp == "A" else ""
    if extra:
        return f"{short}。{extra}{imp_note}"
    return f"{short}。{imp_note}".strip()


def build_exam_focus(term: str, exam_points: list[str]) -> str:
    if not exam_points:
        return ""
    p1 = exam_points[0].rstrip("。")
    if len(exam_points) > 1:
        p2 = exam_points[1].rstrip("。")
        return f"「{term}」の肢では、まず「{p1}」を基準にし、次に「{p2}」に合わない選択肢を除外する読み方が有効です。"
    return f"「{term}」の肢では、「{p1}」に照らして、定義と矛盾する表述を先に除外してください。"


def build_faqs(
    row: dict[str, str],
    related: list[str],
    lookup: dict[str, dict[str, str]],
) -> dict[str, str]:
    term = row["term"].strip()
    defn = norm(row.get("definition"))
    short = norm(row.get("short_def"))
    legal = norm(row.get("legal_basis"))
    sents = split_sentences(defn)

    faq1_a = sents[0] if sents else f"{term}とは、{short.rstrip('。')}。"

    if related and related[0] in lookup:
        rel = related[0]
        rel_s = pick_study_sentences(norm(lookup[rel].get("definition")), 1)
        rel_bit = rel_s[0].rstrip("。") if rel_s else norm(lookup[rel].get("short_def")).rstrip("。")
        faq2_q = f"{term}と{rel}の違いは何ですか？"
        faq2_a = (
            f"{term}は{sents[0].rstrip('。') if sents else short.rstrip('。')}。"
            f"一方、{rel}は{rel_bit}。"
            f"試験では両者の定義で異なる語句（時期・主体・効果）を確認してください。"
        )
    elif any(m in defn for m in REQUIREMENT_MARKERS):
        req_sent = next((s for s in sents if score_sentence(s) >= 3), sents[0] if sents else "")
        faq2_q = f"{term}の要件・注意点は何ですか？"
        faq2_a = req_sent or defn
    else:
        faq2_q = f"{term}はどのような場面で使われますか？"
        faq2_a = sents[1] if len(sents) > 1 else (sents[0] if sents else defn)

    laws = split_semicolon(legal)
    if laws and laws[0] != "—":
        faq3_q = f"{term}の根拠はどこにありますか？"
        faq3_a = f"主な根拠は{'・'.join(laws[:3])}です。条文の要件と、{term}の定義文を対応づけて覚えてください。"
    else:
        faq3_q = f"{term}を覚えるときのポイントは？"
        faq3_a = build_memory_tip(row, related)

    return {
        "faq_1_question": f"{term}とは何ですか？",
        "faq_1_answer": faq1_a,
        "faq_2_question": faq2_q,
        "faq_2_answer": faq2_a,
        "faq_3_question": faq3_q,
        "faq_3_answer": faq3_a,
    }


def meaningful_compare_table(
    term: str,
    row: dict[str, str],
    related: list[str],
    lookup: dict[str, dict[str, str]],
) -> str:
    if term in COMPARE_TABLES:
        return COMPARE_TABLES[term]
    if not related:
        return ""
    rel = related[0]
    if rel not in lookup:
        return ""
    rel_row = lookup[rel]
    defn_t = norm(row.get("definition"))
    defn_r = norm(rel_row.get("definition")) or norm(rel_row.get("short_def"))

    def signals(text: str) -> set[str]:
        found: set[str] = set()
        for m in TIMING_MARKERS + REQUIREMENT_MARKERS + ("更新", "登録", "解除", "終了", "交付", "説明"):
            if m in text:
                found.add(m)
        return found

    sig_t, sig_r = signals(defn_t), signals(defn_r)
    diff = (sig_t | sig_r) - (sig_t & sig_r)
    if len(diff) < 1 and len(sig_t | sig_r) < 2:
        return ""

    rows_html = []
    for label, text in ((term, defn_t), (rel, defn_r)):
        hook = pick_study_sentences(text, 1)
        cell = esc(hook[0][:90] if hook else norm(row.get("short_def"))[:90])
        rows_html.append(f"<tr><th>{esc(label)}</th><td>{cell}</td></tr>")
    if diff:
        rows_html.append(
            "<tr><th>見分け</th><td>"
            + esc("／".join(sorted(diff)[:4]))
            + "</td></tr>"
        )
    return (
        '<table class="seo-info-table"><thead><tr><th>比較</th><th>要点</th></tr></thead><tbody>'
        + "".join(rows_html)
        + "</tbody></table>"
    )


def finish_handcrafted_row(row: dict[str, str], lookup: dict[str, dict[str, str]]) -> None:
    """Fill SEO columns for append_glossary rows without reusing old template fields."""
    term = row["term"].strip()
    related = split_semicolon(row.get("related_terms") or "")
    pts_raw = norm(row.get("exam_points"))
    exam_points = [p.strip() for p in pts_raw.split(";") if p.strip()] if pts_raw else derive_exam_points(row, related)

    if not norm(row.get("summary_body")):
        row["summary_body"] = build_summary_body(row)
    if not norm(row.get("exam_focus")):
        row["exam_focus"] = build_exam_focus(term, exam_points)
    if not norm(row.get("comparison_table")):
        table = meaningful_compare_table(term, row, related, lookup)
        if table:
            row["comparison_table"] = table
    for col in ("exam_focus", "faq_2_answer", "term_detail_body"):
        val = norm(row.get(col))
        for banned in BANNED_PHRASES:
            if banned in val and col == "exam_focus":
                row["exam_focus"] = build_exam_focus(term, exam_points)
                break


def upgrade_row(
    row: dict[str, str],
    lookup: dict[str, dict[str, str]],
    handcrafted: dict[str, dict[str, str]],
) -> bool:
    term = row["term"].strip()
    if term in handcrafted:
        hc = handcrafted[term]
        for key, val in hc.items():
            if val:
                row[key] = val
        if not norm(row.get("article_title")):
            row["article_title"] = f"{term}とは？意味・試験ポイントを整理"
        finish_handcrafted_row(row, lookup)
        return True

    if not norm(row.get("article_title")):
        row["article_title"] = f"{term}とは？意味・試験ポイントを整理"

    related = split_semicolon(row.get("related_terms") or "")
    exam_points = derive_exam_points(row, related)

    row["term_detail_body"] = build_term_detail_body(row, related, lookup)
    row["exam_points"] = ";".join(exam_points)
    row["exam_focus"] = build_exam_focus(term, exam_points)
    row["summary_body"] = build_summary_body(row)
    row["article_lead"] = build_article_lead(row)
    row["common_mistakes"] = build_common_mistakes(row, related)
    row["memory_tip"] = build_memory_tip(row, related)
    row["explanation"] = (
        f"{term}は、{norm(row.get('short_def')).rstrip('。')}。"
        f"試験では{exam_points[0].rstrip('。') if exam_points else '定義と要件'}が問われやすいです。"
    )
    row.update(build_faqs(row, related, lookup))

    table = meaningful_compare_table(term, row, related, lookup)
    row["comparison_table"] = table if table else ""

    imp = norm(row.get("importance") or "B")
    if imp == "A" and term in EXAMPLES:
        q, a = EXAMPLES[term]
        row["example_question"] = q
        row["example_answer"] = a

    return True


def audit_originality(rows: list[dict[str, str]]) -> None:
    for phrase in BANNED_PHRASES:
        n = sum(
            1
            for r in rows
            if phrase in (
                norm(r.get("term_detail_body"))
                + norm(r.get("exam_focus"))
                + norm(r.get("faq_2_answer"))
            )
        )
        if n:
            print(f"  WARN banned phrase {phrase!r}: {n} rows")

    leads = [norm(r.get("article_lead")) for r in rows]
    from collections import Counter

    dup_leads = [(t, c) for t, c in Counter(leads).items() if c > 3]
    if dup_leads:
        print(f"  duplicate article_lead patterns (>3): {len(dup_leads)}")
    else:
        print("  article_lead: no heavy duplication")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    text = CSV_PATH.read_text(encoding="utf-8-sig")
    rows = list(csv.DictReader(text.splitlines()))
    fieldnames = list(rows[0].keys()) if rows else []
    for col in ("summary_body", "comparison_table", "exam_focus"):
        if col not in fieldnames:
            fieldnames.append(col)

    lookup = {r["term"].strip(): r for r in rows}
    handcrafted = load_handcrafted_overrides()
    print(f"Hand-crafted overrides: {len(handcrafted)} terms")

    n = 0
    for row in rows:
        if upgrade_row(row, lookup, handcrafted):
            n += 1

    print(f"Upgraded {n}/{len(rows)} rows")
    print("Originality audit:")
    audit_originality(rows)

    if args.dry_run:
        print("Dry run — CSV not written")
        return 0

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {CSV_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
