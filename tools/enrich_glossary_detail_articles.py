#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Enrich glossary rows that have article_title with detail-article quality content.

Optional: --bootstrap-a N creates detail shells for importance-A terms without article_title.
"""

from __future__ import annotations

import argparse
import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CSV_PATH = ROOT / "data" / "glossary_terms.csv"

EXTRA_COLS = [
    "summary_body",
    "comparison_table",
    "exam_focus",
]

COMPARE_TABLES: dict[str, str] = {
    "締結時書面": """<table class="seo-info-table"><thead><tr><th>書面</th><th>交付時期</th><th>主な根拠</th><th>試験の焦点</th></tr></thead><tbody>
<tr><th>重要事項説明書（重説）</th><td>契約締結前</td><td>宅建35条／賃管13・30条</td><td>説明者・記名・事前交付</td></tr>
<tr><th>締結時書面</th><td>契約成立時</td><td>賃管14条／31条</td><td>遅滞なく交付・記載事項</td></tr>
<tr><th>37条書面（契約書）</th><td>契約成立時</td><td>宅建37条</td><td>宅建士記名・契約内容</td></tr>
</tbody></table>""",
    "35条書面": """<table class="seo-info-table"><thead><tr><th>書面</th><th>時期</th><th>説明者</th><th>覚え方</th></tr></thead><tbody>
<tr><th>35条書面（重説）</th><td>契約前</td><td>宅建士</td><td>35＝前</td></tr>
<tr><th>37条書面</th><td>成立時</td><td>宅建士記名</td><td>37＝後（契約書）</td></tr>
<tr><th>締結時書面（賃管）</th><td>成立時</td><td>管理業者等</td><td>賃管業法の契約書</td></tr>
</tbody></table>""",
    "定期借家": """<table class="seo-info-table"><thead><tr><th>項目</th><th>定期借家</th><th>普通借家</th></tr></thead><tbody>
<tr><th>更新</th><td>原則なし（満了終了）</td><td>法定更新あり</td></tr>
<tr><th>事前説明</th><td>独立書面が必要</td><td>不要（38条の制度）</td></tr>
<tr><th>終了通知</th><td>1年以上は1年前〜6ヵ月前</td><td>更新拒絶通知の論点</td></tr>
<tr><th>減額請求</th><td>特約で排除しうる</td><td>排除特約は無効（強行）</td></tr>
</tbody></table>""",
    "普通借家": """<table class="seo-info-table"><thead><tr><th>項目</th><th>普通借家</th><th>定期借家</th></tr></thead><tbody>
<tr><th>更新</th><td>原則更新（拒絶は正当事由）</td><td>更新なし</td></tr>
<tr><th>期間1年未満</th><td>期間の定めなしとみなす</td><td>38条の要件で別途整理</td></tr>
<tr><th>立退料</th><td>事業用等で論点</td><td>定期は終了通知が中心</td></tr>
</tbody></table>""",
    "基幹業務": """<table class="seo-info-table"><thead><tr><th>要素</th><th>内容</th><th>単独受託</th></tr></thead><tbody>
<tr><th>維持保全</th><td>点検・清掃・修繕等</td><td>管理業務にならない</td></tr>
<tr><th>金銭管理</th><td>家賃・敷金の受領・送金</td><td>管理業務にならない</td></tr>
<tr><th>基幹業務</th><td>募集・契約事務・入居者対応</td><td>管理業務にならない</td></tr>
<tr><th>三者セット</th><td>併せて行う</td><td>管理業務に該当</td></tr>
</tbody></table>""",
    "原状回復ガイドライン": """<table class="seo-info-table"><thead><tr><th>区分</th><th>負担者（原則）</th><th>試験の注意</th></tr></thead><tbody>
<tr><th>通常損耗・経年変化</th><td>貸主</td><td>借主負担とする誤肢</td></tr>
<tr><th>故意・過失による損耗</th><td>借主</td><td>善管注意違反と結びつく</td></tr>
<tr><th>特約・著しい損耗</th><td>契約次第</td><td>ガイドライン＝法律ではない</td></tr>
</tbody></table>""",
    "金銭管理": """<table class="seo-info-table"><thead><tr><th>義務</th><th>内容</th></tr></thead><tbody>
<tr><th>分別管理</th><td>預り金を自己財産と区分</td></tr>
<tr><th>帳簿保存</th><td>入出金の記録・保存</td></tr>
<tr><th>三者セット</th><td>維持保全・基幹業務と併せる</td></tr>
</tbody></table>""",
    "事前書面交付": """<table class="seo-info-table"><thead><tr><th>手続</th><th>時期</th><th>IT重説</th></tr></thead><tbody>
<tr><th>事前書面交付</th><td>説明の前</td><td>ここも必要</td></tr>
<tr><th>重要事項説明</th><td>説明実施</td><td>双方向・承諾</td></tr>
<tr><th>締結時書面</th><td>成立時</td><td>別要件</td></tr>
</tbody></table>""",
    "管理業務": """<table class="seo-info-table"><thead><tr><th>要素</th><th>単独</th><th>三者セット</th></tr></thead><tbody>
<tr><th>維持保全</th><td>管理業務にならない</td><td rowspan="3">併せて行うと管理業務</td></tr>
<tr><th>金銭管理</th><td>管理業務にならない</td></tr>
<tr><th>基幹業務</th><td>管理業務にならない</td></tr>
</tbody></table>""",
    "IT重説": """<table class="seo-info-table"><thead><tr><th>要件</th><th>内容</th></tr></thead><tbody>
<tr><th>双方向性</th><td>映像・音声で質疑応答が可能</td></tr>
<tr><th>事前書面交付</th><td>説明前に書面を渡す</td></tr>
<tr><th>承諾</th><td>相手方の同意が必要</td></tr>
</tbody></table>""",
    "更新拒絶通知": """<table class="seo-info-table"><thead><tr><th>項目</th><th>普通借家</th><th>定期借家</th></tr></thead><tbody>
<tr><th>更新</th><td>拒絶通知（正当事由）</td><td>更新なし</td></tr>
<tr><th>終了</th><td>満了＋拒絶で終了</td><td>終了通知が中心</td></tr>
</tbody></table>""",
    "原状回復": """<table class="seo-info-table"><thead><tr><th>区分</th><th>負担（原則）</th></tr></thead><tbody>
<tr><th>通常損耗</th><td>貸主</td></tr>
<tr><th>故意・過失</th><td>借主</td></tr>
<tr><th>ガイドライン</th><td>実務指針（法令ではない）</td></tr>
</tbody></table>""",
    "建物賃貸借契約": """<table class="seo-info-table"><thead><tr><th>類型</th><th>更新</th><th>試験の焦点</th></tr></thead><tbody>
<tr><th>普通借家</th><td>法定更新あり</td><td>更新拒絶・正当事由</td></tr>
<tr><th>定期借家</th><td>原則なし</td><td>終了通知・事前説明</td></tr>
</tbody></table>""",
    "借主負担特約": """<table class="seo-info-table"><thead><tr><th>費用</th><th>原則</th><th>特約</th></tr></thead><tbody>
<tr><th>通常損耗・経年変化</th><td>貸主負担</td><td>借主負担特約は無効になりうる</td></tr>
<tr><th>故意・過失</th><td>借主負担</td><td>有効な範囲で整理</td></tr>
</tbody></table>""",
    "更新料": """<table class="seo-info-table"><thead><tr><th>項目</th><th>上限・要件</th></tr></thead><tbody>
<tr><th>更新料</th><td>1ヵ月分の家賃を超えない（原則）</td></tr>
<tr><th>合意更新</th><td>新契約として更新料を取りうる</td></tr>
</tbody></table>""",
}

COMPARE_TABLES["定期建物賃貸借契約"] = COMPARE_TABLES["定期借家"]
COMPARE_TABLES["重要事項説明（宅建業法）"] = COMPARE_TABLES["35条書面"]

CATEGORY_PRIORITY = (
    "賃貸住宅管理業法",
    "賃貸借契約",
    "借地借家法",
    "民法",
    "管理実務",
    "原状回復",
    "建物・設備",
    "賃貸経営・PM/AM",
    "会計・税務・保険",
    "関連法令",
)

EXAMPLES: dict[str, tuple[str, str]] = {
    "締結時書面": (
        "管理受託契約が成立したが、締結時書面を後日交付した。適切か。",
        "×。契約成立時に遅滞なく交付する必要がある（賃管業法14条）。",
    ),
    "基幹業務": (
        "維持保全と金銭管理のみを受託し、入居者対応は行わない。管理業務か。",
        "×。基幹業務（募集・契約事務・入居者対応等）も併せて行う場合に管理業務となる。",
    ),
    "定期借家": (
        "定期建物賃貸借で期間満了が近い。貸主は更新拒絶通知を出せばよいか。",
        "×。定期借家は更新がなく、原則として終了通知（1年以上は1年前〜6ヵ月前）の論点。",
    ),
    "無登録営業": (
        "管理戸数250戸を登録なく管理業務を行う。適法か。",
        "×。200戸以上は登録が必要で、無登録営業は罰則対象。",
    ),
    "二重賃貸借": (
        "貸主が同一部屋に後から別の借主と契約した。先の借主はどうなるか。",
        "先に有効な賃借権・引渡しを有する借主が優先し、後の借主は対抗できない場合がある。",
    ),
    "契約不適合責任": (
        "入居後、給湯器が契約時の説明と異なる状態だった。借主は何を求められるか。",
        "修補請求・賃料減額・損害賠償・解除等（契約不適合責任）を検討できる。",
    ),
    "建物明渡請求": (
        "賃料滞納のみで、契約を解除せず明渡しを求めた。認められるか。",
        "×。賃貸借を終了（解除・満了等）させたうえで明渡しを求める。",
    ),
    "管理業務": (
        "維持保全のみを受託している。賃貸住宅管理業法上の管理業務か。",
        "×。維持保全と金銭管理に加え基幹業務を併せて行う場合に管理業務となる。",
    ),
    "IT重説": (
        "事前書面交付なしでIT重説のみ実施した。適法か。",
        "×。事前書面交付と相手方の承諾が必要。",
    ),
    "更新拒絶通知": (
        "定期借家契約満了前に、貸主が更新拒絶通知を出した。適切か。",
        "×。定期借家は更新がなく、終了通知の制度が中心。",
    ),
    "定期建物賃貸借契約": (
        "定期建物賃貸借で、貸主は更新拒絶通知を出せば満了後に終了できるか。",
        "×。定期借家は更新がなく、終了通知（期間に応じた通知期限）の論点。",
    ),
    "正当事由": (
        "貸主の親族の入居を理由に更新拒絶した。正当事由に当たるか。",
        "○。自己使用等は正当事由の典型（具体事情で判断）。",
    ),
    "借主負担特約": (
        "原状回復で経年変化分も借主負担とする特約のみを結んだ。有効か。",
        "×。通常損耗・経年変化は貸主負担が原則で、借主負担特約は無効になりうる。",
    ),
    "更新料": (
        "更新時に家賃の2ヵ月分を更新料として請求した。適法か。",
        "×。更新料は原則1ヵ月分の家賃を超えない。",
    ),
    "強行規定（借地借家法）": (
        "借主不利の特約で更新拒絶の要件を緩和した。有効か。",
        "×。借地借家法の強行規定に反する特約は無効。",
    ),
}

CUSTOM_LEADS: dict[str, str] = {
    "締結時書面": "賃管業法上、契約が成立した瞬間に交付する書面です。重要事項説明（契約前）や宅建37条書面（成立時）と交付時期が違うため、試験では「いつ・誰が・何を渡すか」を表で整理して覚えるのが近道です。",
    "原状回復ガイドライン": "国交省等の実務指針で、原状回復費用の負担区分を示します。法律そのものではありませんが、通常損耗・経年変化と故意過失の線引きは頻出です。",
    "定期借家": "更新がなく期間満了で終了する借家の総称です。普通借家との比較表が試験の定番なので、終了通知・事前説明の有無までセットで押さえてください。",
    "定期建物賃貸借契約": "借地借家法38条の制度です。普通借家との違い（更新なし・終了通知・事前説明）を表で整理して覚えると、肢分けが速くなります。",
    "更新拒絶通知": "普通借家の更新を拒む手続です。定期借家には更新がないため、通知の種類と期限を取り違えないことが試験の焦点です。",
    "管理受託契約": "賃管業法の中心契約です。重説・締結時書面・管理業務の範囲がセットで問われるため、書面交付の時期から押さえてください。",
}


def split_legal(legal: str) -> str:
    if not legal:
        return "関連法令"
    return legal.replace(";", "・").replace("—", "・")


def apply_enrichment(row: dict[str, str], updates: dict[str, str], *, preserve_rich: bool) -> None:
    for key, value in updates.items():
        if not value:
            continue
        existing = (row.get(key) or "").strip()
        if preserve_rich and key in ("explanation", "exam_points") and len(existing) > 80:
            continue
        row[key] = value


def enrich_row(row: dict[str, str]) -> dict[str, str]:
    term = row["term"].strip()
    short = (row.get("short_def") or "").strip()
    defn = (row.get("definition") or "").strip()
    cat = (row.get("category") or "").strip()
    legal = (row.get("legal_basis") or "").strip()
    related = [x.strip() for x in (row.get("related_terms") or "").split(";") if x.strip()]
    rel_join = "、".join(related[:3]) if related else "関連用語"
    imp = (row.get("importance") or "B").strip()

    summary_body = (
        f"{short.rstrip('。')}。"
        f"{term}は{cat}分野で繰り返し問われるキーワードで、"
        f"意味だけでなく要件の有無（時期・主体・承諾・数値）まで確認する必要があります。"
    )

    detail_p2 = (
        f"実務上は、{term}が具体的手続に落とし込まれることで、当事者間の説明責任やトラブル防止につながります。"
        f"特に{rel_join}と並べて学ぶと、選択肢の「似ているが違う」表述を見分けやすくなります。"
    )
    detail_p3 = (
        f"試験では{split_legal(legal)}を根拠に、定義・要件・効果（義務違反・監督処分・民事効果）を"
        f"一文ずつ説明できる状態を目標にしてください。過去問で読み飛ばした語は、本ページで整理してから演習に戻ると定着します。"
    )
    term_detail_body = f"{defn}\n\n{detail_p2}\n\n{detail_p3}"

    exam_pts_raw = row.get("exam_points") or ""
    pts = [p.strip() for p in exam_pts_raw.split(";") if p.strip()]
    exam_focus = (
        f"選択肢では、{term}の名称だけに反応して結論を急ぐ誤りが多く見られます。"
        f"正解・誤りを判断するときは、"
        + (pts[0] if pts else "定義と要件")
        + "を基準に、主体・時期・承諾・数値の有無をチェックしてください。"
    )
    if len(pts) > 1:
        exam_focus += f" さらに「{pts[1]}」の要件を満たさない肢は消去、残りで最も正確な表述を選びます。"
    exam_focus += (
        f" 関連する{rel_join}と混同する肢が出たら、"
        f"それぞれの制度の目的（借主保護・管理業務の適正化・金銭管理など）を一言で言い分けられると強くなります。"
    )

    mistakes = (
        f"「{term}」を単語暗記だけで済ませ、具体要件まで確認しないと誤答しやすいです。"
        f"また、{rel_join}と同一視する選択肢にも注意が必要です。"
        f"ガイドライン・実務慣行と法令の強行規定を取り違える問題では、"
        f"「実務上そうだから正しい」ではなく根拠条文で判断してください。"
    )

    memory = (
        f"{term}＝{split_legal(legal)}。"
        f"関連（{rel_join}）は比較表で整理。"
        f"試験直前は要件のチェックリスト（誰が・いつ・何を）を見直す。"
    )

    article_lead = CUSTOM_LEADS.get(
        term,
        f"{cat}分野の頻出語です。{short.rstrip('。')}。"
        f"本記事では定義に加え、試験で落とし穴になりやすい条件と関連用語の違いを整理します。",
    )

    explanation = (
        f"{term}は、{short.rstrip('。')}。"
        f"試験では{pts[0] if pts else '定義と要件'}が問われやすく、"
        f"{rel_join}との違いを説明できると得点につながります。"
    )

    out: dict[str, str] = {
        "summary_body": summary_body,
        "term_detail_body": term_detail_body,
        "article_lead": article_lead,
        "explanation": explanation,
        "exam_focus": exam_focus,
        "common_mistakes": mistakes,
        "memory_tip": memory,
    }

    if term in COMPARE_TABLES and COMPARE_TABLES[term]:
        out["comparison_table"] = COMPARE_TABLES[term]

    if imp == "A" and term in EXAMPLES:
        q, a = EXAMPLES[term]
        out["example_question"] = q
        out["example_answer"] = a
    elif imp == "A":
        out["example_question"] = f"「{term}」に関する次の記述として、最も適切なものはどれか（概念確認）。"
        out["example_answer"] = f"{short.rstrip('。')}。詳細は本文の試験ポイントと関連用語を参照。"

    # Longer FAQ
    for i in (1, 2):
        qk, ak = f"faq_{i}_question", f"faq_{i}_answer"
        if row.get(qk) and row.get(ak) and len(row[ak]) < 120:
            out[ak] = (
                f"{row[ak]}"
                f" 本記事の比較表・試験ポイントとあわせ、関連用語（{rel_join}）のページも確認すると理解が安定します。"
            )

    return out


def bootstrap_row(row: dict[str, str]) -> None:
    term = row["term"].strip()
    if not (row.get("article_title") or "").strip():
        row["article_title"] = f"{term}とは？意味・試験ポイントを整理"
    if not (row.get("faq_1_question") or "").strip():
        row["faq_1_question"] = f"{term}の定義を一言で言えますか？"
        row["faq_1_answer"] = (row.get("short_def") or row.get("definition") or "").strip()
    if not (row.get("faq_2_question") or "").strip():
        row["faq_2_question"] = f"{term}は試験で何と比較されますか？"
        rel = [x.strip() for x in (row.get("related_terms") or "").split(";") if x.strip()]
        row["faq_2_answer"] = (
            f"関連用語（{'、'.join(rel[:3]) if rel else '同分野の近い語'}）との違いを押さえると得点しやすいです。"
        )


def select_bootstrap_targets(
    rows: list[dict[str, str]],
    limit: int,
    *,
    importance: str | None = None,
) -> list[dict[str, str]]:
    prio = {c: i for i, c in enumerate(CATEGORY_PRIORITY)}
    imp_order = {"A": 0, "B": 1, "C": 2}
    cands = [
        r
        for r in rows
        if not (r.get("article_title") or "").strip()
        and (importance is None or (r.get("importance") or "").strip() == importance)
    ]
    cands.sort(
        key=lambda r: (
            prio.get((r.get("category") or "").strip(), 99),
            imp_order.get((r.get("importance") or "").strip(), 9),
            r["term"],
        )
    )
    return cands[:limit] if limit > 0 else cands


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--bootstrap-a",
        type=int,
        metavar="N",
        help="Create detail shells for N importance-A terms without article_title, then enrich",
    )
    parser.add_argument(
        "--bootstrap-b",
        type=int,
        metavar="N",
        help="Create detail shells for N importance-B terms without article_title, then enrich",
    )
    parser.add_argument(
        "--bootstrap-c",
        type=int,
        metavar="N",
        help="Create detail shells for N importance-C terms without article_title, then enrich",
    )
    parser.add_argument(
        "--bootstrap-all",
        action="store_true",
        help="Bootstrap every term still missing article_title (A→B→C by category)",
    )
    args = parser.parse_args()

    text = CSV_PATH.read_text(encoding="utf-8-sig")
    rows = list(csv.DictReader(text.splitlines()))
    fieldnames = list(rows[0].keys()) if rows else []
    for col in EXTRA_COLS + ["exam_focus", "comparison_table"]:
        if col not in fieldnames:
            fieldnames.append(col)

    booted_terms: set[str] = set()

    def bootstrap_batch(importance: str | None, limit: int, label: str) -> None:
        batch = select_bootstrap_targets(rows, limit, importance=importance)
        for row in batch:
            bootstrap_row(row)
            booted_terms.add(row["term"].strip())
        if batch:
            print(f"Bootstrapped {len(batch)} {label} detail shells")

    if args.bootstrap_all:
        bootstrap_batch(None, 0, "remaining")
    else:
        if args.bootstrap_a:
            bootstrap_batch("A", args.bootstrap_a, "A-importance")
        if args.bootstrap_b:
            bootstrap_batch("B", args.bootstrap_b, "B-importance")
        if args.bootstrap_c:
            bootstrap_batch("C", args.bootstrap_c, "C-importance")

    n = 0
    for row in rows:
        if not (row.get("article_title") or "").strip():
            continue
        apply_enrichment(
            row,
            enrich_row(row),
            preserve_rich=row["term"].strip() in booted_terms,
        )
        n += 1

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"Enriched {n} detail articles in {CSV_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
