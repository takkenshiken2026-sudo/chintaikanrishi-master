#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Improve all glossary detail articles for readability:
- Plain, accessible Japanese throughout
- summary_body with concrete examples
- Expanded memory_tip (structured)
- 3-4 FAQ items per term

Run: python3 tools/improve_glossary_readability.py
Then: python3 tools/build_glossary_pages.py  (or build_all.py)
"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CSV_PATH = ROOT / "data" / "glossary_terms.csv"

# Formal → plain replacements (order matters)
PLAIN_REPLACEMENTS: list[tuple[str, str]] = [
    ("及び", "と"),
    ("並びに", "と"),
    ("において", "では"),
    ("に関して", "について"),
    ("することができる", "できる"),
    ("することができない", "できない"),
    ("となりうる", "になることがある"),
    ("となり得る", "になることがある"),
    ("いう", "言う"),
    ("当該", "その"),
    ("又は", "または"),
    ("若しくは", "または"),
    ("ただし", "ただし、"),
    ("旨", "内容"),
    ("に際して", "のとき"),
]


def norm(s: str | None) -> str:
    return (s or "").strip()


def split_semicolon(s: str) -> list[str]:
    return [x.strip() for x in (s or "").split(";") if x.strip()]


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", text or "").strip()
    if not text:
        return []
    return [p.strip() for p in re.findall(r"[^。！？]+[。！？]?", text) if p.strip()]


def plain_text(text: str) -> str:
    if not text:
        return ""
    t = text
    for old, new in PLAIN_REPLACEMENTS:
        t = t.replace(old, new)
    return t


def parse_numbered(defn: str) -> list[str]:
    return [p.strip().rstrip("。") for p in re.findall(r"[①②③④⑤]([^①②③④⑤]+)", defn)]


def concrete_example(row: dict[str, str], related: list[str]) -> str:
    term = row["term"].strip()
    cat = norm(row.get("category"))
    short = norm(row.get("short_def")).rstrip("。")
    defn = norm(row.get("definition"))

    # Term-specific high-value examples
    specific: dict[str, str] = {
        "IT重説": (
            "例えば、遠方の借主に部屋を紹介するとき、事前に説明書（重説）をメール等で渡し、"
            "借主がオンライン説明を受けることに同意したうえで、ビデオ通話で質疑応答しながら説明する、"
            "という流れがイメージしやすいです。"
        ),
        "締結時書面": (
            "例えば、管理受託契約の打ち合わせが終わり口頭で「契約成立」と言った瞬間に、"
            "契約内容が書かれた書面を渡さないまま後日送付するのは要件を満たしません。"
            "成立したらその場（または遅滞なく）交付するイメージです。"
        ),
        "定期借家": (
            "例えば、2年間の定期借家契約なら、期間が終われば原則として契約は終了します。"
            "普通借家のように「自動更新」されるわけではないので、"
            "貸主はあらかじめ決められた方法で終了の通知を行う必要があります。"
        ),
        "普通借家": (
            "例えば、1年契約が満了しても、貸主が正当事由なく更新を拒まなければ、"
            "同じ条件で契約が続く（法定更新）イメージを持ってください。"
        ),
        "原状回復": (
            "例えば、退去時に壁紙の色あせだけが目立つ場合、経年変化として貸主負担になりやすく、"
            "釘穴を無断で開けた場合は借主負担の論点になります。"
        ),
        "管理業務": (
            "例えば、清掃と家賃の受領だけを受託し、入居者対応や契約事務を行わない場合は、"
            "「管理業務」には当たらない、という整理が試験で問われます。"
        ),
        "敷金": (
            "例えば、入居時に預かった敷金10万円は、退去・明渡しのあと、"
            "未払賃料や原状回復費を差し引いた残額を返還する、という流れで理解します。"
        ),
        "更新拒絶通知": (
            "例えば、普通借家で契約期間が満了する前に、貸主が「更新しない」旨を"
            "決められた期間・方法で借主に伝える手続が、更新拒絶通知です。"
            "定期借家では更新自体がないため、別の「終了通知」の論点になります。"
        ),
    }
    if term in specific:
        return specific[term]

    numbered = parse_numbered(defn)
    if numbered:
        return (
            f"例えば、この制度では「{numbered[0]}」がポイントです。"
            f"選択肢では、{numbered[-1][:40]}…のような一部だけ正しい肢に注意してください。"
        )

    if related and "契約" in defn:
        return (
            f"例えば、契約の流れのなかで「{term}」がどの段階（説明前・成立時・入居後など）に"
            f"関わるかをイメージすると、{related[0]}などの近い用語と混同しにくくなります。"
        )

    by_cat: dict[str, str] = {
        "賃貸住宅管理業法": (
            f"例えば、管理会社がオーナーから業務を受託する場面で「{term}」がどこで効くか"
            f"（登録・書面・預り金など）を想像すると理解しやすいです。"
        ),
        "借地借家法": (
            f"例えば、入居者とオーナーの賃貸借の続き方（更新するか・期間満了で終わるか）を"
            f"考えるときに「{term}」が出てくる、というイメージで押さえてください。"
        ),
        "民法": (
            f"例えば、トラブルが起きたあと（支払わない・契約を終了させたい等）に"
            f"「{term}」がどう使われるかを想定すると、試験の選択肢が読みやすくなります。"
        ),
        "管理実務": (
            f"例えば、入居者からの連絡や滞納が発生したとき、現場ではどの順番で"
            f"「{term}」に関する手続を踏むかをイメージしておくと実務・試験の両方に役立ちます。"
        ),
        "原状回復": (
            f"例えば、退去時の費用負担で「誰がいくら払うか」を決める場面で"
            f"「{term}」の考え方が使われます。"
        ),
        "建物・設備": (
            f"例えば、点検記録や修繕の依頼が発生したとき、"
            f"「{term}」が誰の義務・どの設備に関わるかを確認する場面で使われます。"
        ),
        "賃貸経営・PM/AM": (
            f"例えば、家賃収入や空室、修繕費を見るときに「{term}」が"
            f"経営判断の指標として使われます。"
        ),
        "会計・税務・保険": (
            f"例えば、オーナーが確定申告や保険の手続をするときに"
            f"「{term}」が収支や税務の整理に関わります。"
        ),
        "関連法令": (
            f"例えば、賃貸管理以外の法令（消防・区分所有・民泊など）が絡む場面で"
            f"「{term}」の義務主体が誰かを確認する、という使い方です。"
        ),
        "賃貸借契約": (
            f"例えば、仲介会社が部屋を紹介して契約書にサインする流れのなかで、"
            f"「{term}」がいつ・誰によって必要になるかを考えると覚えやすいです。"
        ),
    }
    return by_cat.get(
        cat,
        f"例えば、{short}という場面を頭に置き、誰が・いつ・何をするかを"
        f"セットで思い出せるようにしておくとよいです。",
    )


def build_summary_body(row: dict[str, str], related: list[str]) -> str:
    term = row["term"].strip()
    short = norm(row.get("short_def")).rstrip("。")
    defn = norm(row.get("definition"))
    lead_sent = split_sentences(defn)[0].rstrip("。") if split_sentences(defn) else short

    p1 = plain_text(
        f"「{term}」を一言でいうと、{short}です。"
        f"わかりやすく言い換えると、{lead_sent}。"
    )
    example = plain_text(concrete_example(row, related))
    p3 = plain_text(
        "試験では、定義をそのまま暗記するだけでなく、"
        "具体例のように「誰が・いつ・どうなるか」まで説明できると安心です。"
    )
    return f"{p1}\n\n【具体例】\n{example}\n\n【試験のポイント】\n{p3}"


def build_memory_tip(row: dict[str, str], related: list[str], exam_points: list[str]) -> str:
    term = row["term"].strip()
    short = norm(row.get("short_def")).rstrip("。")
    legal = split_semicolon(norm(row.get("legal_basis")))
    numbered = parse_numbered(norm(row.get("definition")))

    one_liner = short
    if numbered:
        one_liner = f"{len(numbered)}つの要素（" + "／".join(numbered[:2]) + "…）"

    steps: list[str] = []
    if numbered:
        for i, n in enumerate(numbered[:3], 1):
            steps.append(f"{i}. {plain_text(n)}")
    elif exam_points:
        for i, p in enumerate(exam_points[:3], 1):
            steps.append(f"{i}. {plain_text(p.rstrip('。'))}")
    else:
        steps = [
            f"1. 「{short}」を言える",
            "2. 根拠条文を言える",
            "3. 関連用語との違いを一言で言える",
        ]

    checks = [
        "定義文と選択肢の主語（誰の義務・権利か）が一致しているか",
        "時期（前・成立時・満了時など）を取り違えていないか",
    ]
    if related:
        checks.append(f"「{related[0]}」と同じ制度だと思い込んでいないか")
    if legal and legal[0] != "—":
        checks.append(f"根拠（{legal[0]}）を確認したか")

    rel_line = ""
    if related:
        rel_line = f"\n\n【関連語とセット】\n「{related[0]}」と表で比較して覚えると、似た肢を落としやすくなります。"

    law_line = ""
    if legal and legal[0] != "—":
        law_line = f"根拠は「{'・'.join(legal[:2])}」です。"

    return (
        f"【一言で覚える】\n{one_liner}。{law_line}\n\n"
        f"【整理のしかた】\n"
        + "\n".join(steps)
        + "\n\n"
        f"【試験で確認すること】\n"
        + "\n".join(f"・{c}" for c in checks)
        + rel_line
    )


def build_faqs(row: dict[str, str], lookup: dict[str, dict[str, str]], related: list[str]) -> dict[str, str]:
    term = row["term"].strip()
    short = norm(row.get("short_def"))
    defn = plain_text(norm(row.get("definition")))
    legal = split_semicolon(norm(row.get("legal_basis")))
    mistakes = norm(row.get("common_mistakes"))

    faq1_a = (
        f"{term}とは、{short.rstrip('。')}です。"
        f"{split_sentences(defn)[0].rstrip('。') if split_sentences(defn) else ''}。"
        f"専門用語が並んでいて難しく感じても、上の一文を起点に読めば大丈夫です。"
    )

    rel_key = related[0] if related else ""
    rel_row = lookup.get(rel_key) if rel_key else None
    if not rel_row and related:
        for k, v in lookup.items():
            if rel_key in k or k in rel_key:
                rel_row = v
                rel_key = k
                break
    if rel_row:
        rel = rel_key
        rel_short = norm(rel_row.get("short_def")).rstrip("。")
        faq2_q = f"{term}と{rel}の違いは何ですか？"
        faq2_a = (
            f"{term}は「{short.rstrip('。')}」が中心です。"
            f"一方、{rel}は「{rel_short}」です。"
            f"試験では、定義の違う部分（時期・主体・効果）を短く言い分けられるかがポイントになります。"
        )
    else:
        faq2_q = f"{term}はいつ問題になりますか？"
        faq2_a = (
            f"契約の説明・成立、入居中のトラブル、退去・精算など、"
            f"場面によって使われ方が変わります。{concrete_example(row, related).replace('例えば、', '')}"
        )

    faq3_q = f"{term}で試験をするときの注意点は？"
    faq3_a = (
        mistakes
        if mistakes
        else f"用語名だけに反応して、定義の条件まで読まない誤りに注意してください。"
    )

    if legal and legal[0] != "—":
        faq4_q = f"{term}の根拠はどこを見ればよいですか？"
        faq4_a = (
            f"主な根拠は{'・'.join(legal[:3])}です。"
            f"条文の見出しと、本ページの定義を対応づけて覚えると復習が楽になります。"
            f"数値や期限は改正で変わることがあるので、本番前に公式情報も確認してください。"
        )
    else:
        faq4_q = f"{term}を復習するときのおすすめの順番は？"
        faq4_a = (
            f"①短い定義を言う → ②具体例を思い出す → ③関連語と比較、の順がおすすめです。"
            f"過去問で出たら、迷った理由（時期・主体・数値）をメモしておくと定着します。"
        )

    return {
        "faq_1_question": f"{term}とは何ですか？（やさしく）",
        "faq_1_answer": plain_text(faq1_a),
        "faq_2_question": faq2_q,
        "faq_2_answer": plain_text(faq2_a),
        "faq_3_question": faq3_q,
        "faq_3_answer": plain_text(faq3_a),
        "faq_4_question": faq4_q,
        "faq_4_answer": plain_text(faq4_a),
    }


def simplify_body(body: str, term: str) -> str:
    if not body:
        return ""
    paras = [p.strip() for p in re.split(r"\n{2,}", body.strip()) if p.strip()]
    out: list[str] = []
    for para in paras:
        if para.startswith("【") or para.startswith("<table"):
            out.append(para)
            continue
        plain = plain_text(para)
        # Remove repetitive agent filler
        for junk in (
            "定義語句（主体・要件・効果）を、そのまま再現",
            "肢の主語・時期・効果が定義と一致",
            "そのまま得点差になります",
        ):
            if junk in plain:
                plain = plain.replace(junk, "定義と要件を確認")
        out.append(plain)
    return "\n\n".join(out)


def simplify_lead(lead: str, term: str, short: str, category: str) -> str:
    lead = plain_text(lead)
    if "頻出です。定義を暗記" in lead or "引っかけ肢が作られやすい" in lead:
        return (
            f"「{term}」は、{plain_text(short.rstrip('。'))}という意味です。"
            f"{category}の問題でよく出るので、意味だけでなく「いつ・誰に」関係するかまで"
            f"セットで覚えておきましょう。"
        )
    return lead


def improve_row(row: dict[str, str], lookup: dict[str, dict[str, str]]) -> None:
    term = row["term"].strip()
    related = split_semicolon(row.get("related_terms") or "")
    exam_points = [p.strip() for p in norm(row.get("exam_points")).split(";") if p.strip()]

    row["summary_body"] = build_summary_body(row, related)
    row["memory_tip"] = build_memory_tip(row, related, exam_points)
    row.update(build_faqs(row, lookup, related))

    if norm(row.get("article_lead")):
        row["article_lead"] = simplify_lead(
            row["article_lead"], term, norm(row.get("short_def")), norm(row.get("category"))
        )
    if norm(row.get("term_detail_body")):
        row["term_detail_body"] = simplify_body(row["term_detail_body"], term)
    if norm(row.get("common_mistakes")):
        row["common_mistakes"] = plain_text(row["common_mistakes"])
    if norm(row.get("explanation")):
        row["explanation"] = plain_text(
            f"{term}は、{norm(row.get('short_def')).rstrip('。')}。"
            f"試験では、具体例のように場面を想像しながら定義を確認すると得点しやすくなります。"
        )
    if norm(row.get("exam_focus")):
        row["exam_focus"] = plain_text(row["exam_focus"])


def main() -> int:
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    fieldnames = list(rows[0].keys()) if rows else []
    for col in ("faq_4_question", "faq_4_answer"):
        if col not in fieldnames:
            fieldnames.append(col)

    lookup = {r["term"].strip(): r for r in rows}
    for row in rows:
        improve_row(row, lookup)

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    # Quality checks
    faq4 = sum(1 for r in rows if norm(r.get("faq_4_answer")))
    summary_ex = sum(1 for r in rows if "【具体例】" in norm(r.get("summary_body")))
    memory_struct = sum(1 for r in rows if "【一言で覚える】" in norm(r.get("memory_tip")))
    print(f"Improved {len(rows)} terms in {CSV_PATH}")
    print(f"  summary with 具体例: {summary_ex}/{len(rows)}")
    print(f"  structured memory_tip: {memory_struct}/{len(rows)}")
    print(f"  faq_4 filled: {faq4}/{len(rows)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
