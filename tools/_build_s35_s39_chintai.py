#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate write_chintai_hub_s35-s39_content.py and premium FAQ block."""

from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(__file__).resolve().parent

from _hub_content_emit import emit_cmp, emit_mis, emit_num, fix_entry  # noqa: E402
from hub_s35_s44_numbers_patches import SLUG_BASE_PATCHES  # noqa: E402

with (ROOT / "data/glossary_terms.csv").open(encoding="utf-8-sig") as _f:
    GLOSS = {r["term"] for r in csv.DictReader(_f)}

_OFFICIAL_TAIL = (
    "賃管試験では用語集と条文の対応づけが得点の鍵になります。"
    "最新の試験要項もあわせて確認してください。"
)


def _rel(*terms: str) -> str:
    ok = [t for t in terms if t in GLOSS]
    for d in ("借地借家法", "敷金", "更新料", "普通借家", "賃貸不動産経営管理士", "管理受託契約", "火災保険"):
        if len(ok) >= 2:
            break
        if d in GLOSS and d not in ok:
            ok.append(d)
    return ";".join(ok[:3])


def _t(title: str, batch: str) -> str:
    return f"{title}（{batch}）"


def _faq(qa: list[tuple[str, str]]) -> list[tuple[str, str]]:
    return [(q, a if len(a) >= 100 else a + _OFFICIAL_TAIL) for q, a in qa]


# (slug_base, theme, cat, compare pair, num tag, num highlight, mistake pair)
THEMES = [
    ("nyukyosha-taiou", "入居者対応", "P", ("入居者苦情対応", "修繕手配"), "入居者対応;管理受託契約", "法定24時間義務なし（実務目安）", ("入居者対応", "管理業務報告")),
    ("shuuzen-hiyou", "修繕費用負担", "S", ("借主負担特約", "原状回復"), "原状回復;修繕費用", "通常損耗は貸主負担（目安）", ("原状回復", "修繕費用")),
    ("chintai-kaitei", "賃料改定", "S", ("賃料改定の協議", "更新料"), "賃料改定;合意更新", "更新料1ヶ月上限（賃料改定とは別）", ("賃料改定の協議", "更新料")),
    ("kanri-houkoku", "管理業務報告", "L", ("管理業務報告", "管理受託契約"), "管理業務報告;管理受託契約", "報告頻度は受託契約で定める", ("管理業務報告", "管理受託契約")),
    ("juyo-jusetsu", "重要事項説明", "L", ("管理受託契約重要事項説明", "IT重説"), "IT重説;重要事項説明（宅建業法）", "説明前に書面交付（目安）", ("管理受託契約重要事項説明", "IT重説")),
    ("sublease-unyou", "サブリース運用", "E", ("サブリーススキーム", "管理受託契約"), "サブリース契約;成約家賃", "空室リスク配分（スキーム次第）", ("サブリーススキーム", "管理受託契約")),
    ("kasai-jishin", "火災・地震", "P", ("火災保険", "地震保険"), "火災保険;地震保険", "契約者・受益者は契約次第", ("火災保険", "地震保険")),
    ("keiyaku-shomen", "契約書面", "L", ("管理受託契約書面", "管理受託契約重要事項説明"), "管理受託契約;重要事項説明", "書面締結・重説前交付", ("管理受託契約書面", "管理受託契約重要事項説明")),
    ("azukari-kanri", "預り金管理", "L", ("分別管理義務", "敷金"), "分別管理義務;敷金", "預かった額の全額を分別", ("分別管理義務", "敷金")),
    ("shiken-hanrei", "試験頻出判例", "E", ("サブリース判例（最高裁平成15.10.21判決等）", "サブリースガイドライン"), "サブリース判例;特定賃貸借", "判例・ガイドライン併読", ("サブリース判例（最高裁平成15.10.21判決等）", "サブリースガイドライン")),
]

BATCH_ANGLE = {
    "S35": "基礎整理",
    "S36": "実務連動",
    "S37": "試験頻出",
    "S38": "判例・ガイド",
    "S39": "横断総合",
}


def _cmp(slug, title, cat, t1, t2, summary, lead, points, mistakes, tip, rel, qa):
    return {
        "slug": slug, "title": title, "cat": cat, "tags": f"{t1};{t2}",
        "summary": summary, "labels": f"{t1};{t2}",
        "axes": [
            ("主体", [f"{t1}の論点", f"{t2}の論点"]),
            ("目的", ["試験頻出", "実務連動"]),
            ("手続", ["書面・説明", "契約・届出"]),
            ("試験", [f"「{t1}＝{t2}」", "「同一制度」"]),
            ("混同", ["主体逆転", "法令取違え"]),
        ],
        "article_title": f"{title}｜賃貸不動産経営管理士",
        "lead": lead,
        "points": points, "mistakes": mistakes, "tip": tip, "related": rel,
        "qa": _faq(qa),
    }


def _num(slug, title, cat, tag, summary, highlight, lead, points, mistakes, tip, rel, qa, slug_base: str):
    patch = SLUG_BASE_PATCHES.get(slug_base)
    if patch:
        items = [(r["item"], r["value"], r["note"]) for r in patch["item_rows"]]
        highlight = patch["highlight"]
        lead = patch["article_lead"]
        points = patch["exam_points"]
        mistakes = patch["common_mistakes"]
        tip = patch["memory_tip"]
        tag = patch.get("tags", tag)
    else:
        items = [
            ("数値", highlight.split("（")[0], "試験頻出"),
            ("根拠", "法令・要項", "条文確認"),
            ("対象", tag.split(";")[0], "適用範囲"),
            ("試験", "混同肢", "正誤確認"),
            ("確認", "用語集", "最新要項"),
        ]
    return {
        "slug": slug, "title": title, "cat": cat, "tags": tag, "summary": summary,
        "highlight": highlight,
        "items": items,
        "article_title": f"{title}｜数値早見",
        "lead": lead, "points": points, "mistakes": mistakes, "tip": tip, "related": rel,
        "qa": _faq(qa),
    }


def _mis(slug, title, cat, t1, t2, summary, lead, points, mistakes, tip, rel, qa):
    return {
        "slug": slug, "title": title, "cat": cat, "tags": f"{t1};{t2}",
        "summary": summary, "confusion": f"{t1}と{t2}の混同。",
        "patterns": [
            ("主体", "逆転", "正しい主体", "主体誤"),
            ("手続", "省略", "法定手続", "手続誤"),
            ("数値", "固定誤", "条文確認", "数値誤"),
            ("効果", "同一", "別制度", "効果誤"),
        ],
        "article_title": f"{title}｜賃貸不動産経営管理士",
        "lead": lead, "points": points, "mistakes": mistakes, "tip": tip, "related": rel,
        "qa": _faq(qa),
    }


def _batch(batch: str) -> tuple[list, list, list]:
    sfx = f"-{batch.lower()}"
    angle = BATCH_ANGLE[batch]
    cmp_rows, num_rows, mis_rows = [], [], []
    for slug_base, theme, cat, (t1, t2), tag, highlight, (m1, m2) in THEMES:
        cmp_rows.append(_cmp(
            f"{slug_base}-cmp{sfx}", _t(f"{theme}：{t1}と{t2}の比較", batch), cat, t1, t2,
            f"{theme}（{angle}）として{t1}と{t2}の関係を整理します。",
            f"{theme}の{angle}として主体・手続・数値を表で整理し、過去問の言い換え肢に対応できるようにしてください。",
            f"{t1}と{t2}を分離;主体確認;書面・届出;試験の正誤肢に注意",
            f"{t1}＝{t2};主体逆転;手続省略;試験の正誤肢に注意",
            f"「{t1}と{t2}を分ける」。", _rel(t1, t2),
            [
                (f"{t1}の要点は？", f"{theme}の{angle}として{t1}の定義・主体・効果を用語集で確認してください。"),
                (f"{t2}との違いは？", f"{t2}は別枠の制度です。{theme}の観点で比較表を作成してください。"),
                ("試験対策の進め方は？", f"{theme}の過去問で主体・手続・数値の三層表を作成し、正誤肢を分類してください。"),
                ("確認先はどこですか？", "用語集と賃貸住宅管理業法・借地借家法を参照してください。"),
            ],
        ))
        num_rows.append(_num(
            f"{slug_base}-num{sfx}", _t(f"{theme}：{highlight.split('（')[0]}の数値", batch), cat, tag,
            f"{theme}（{angle}）の数値・期限を整理します。", highlight,
            f"{theme}の数値は年度・条文で変わる場合があるため、学習中も最新要項で確認してください。",
            f"{highlight};条文確認;混同禁止;用語集参照",
            "数値固定暗記;条文無視;混同;試験の正誤肢に注意",
            f"「{highlight.split('（')[0]}を確認」。", _rel(*tag.split(";")),
            [
                ("数値の要点は？", f"{theme}の{angle}として正確な数値は借地借家法・賃管法・試験要項で確認してください。"),
                ("試験の引っかけは？", f"{theme}で類似制度の数値を当てはめる肢に注意し、制度ごとに色分けしてください。"),
                ("試験対策の進め方は？", f"{theme}の数値一覧表を作成し、過去問の正誤を反復してください。"),
                ("確認先はどこですか？", "借地借家法・賃管法・協議会要項を参照してください。"),
            ],
            slug_base,
        ))
        mis_rows.append(_mis(
            f"{slug_base}-mis{sfx}", _t(f"{theme}：{m1}と{m2}の混同誤り", batch), cat, m1, m2,
            f"{theme}（{angle}）で{m1}と{m2}を同一視する典型誤りを整理します。",
            f"{theme}の正しい整理を表にまとめ、過去問の典型誤答肢を分類してください。",
            f"{m1}≠{m2};主体・手続・数値を分離;用語集参照",
            "同一視;主体逆転;手続省略;試験の正誤肢に注意",
            f"「{m1}と{m2}は別制度」。", _rel(m1, m2),
            [
                ("誤りの内容は何ですか？", f"{theme}の{angle}として試験では言い換え肢として頻出です。"),
                ("正しい理解は何ですか？", f"{m1}と{m2}を主体・手続・効果で分けて整理してください。"),
                ("試験対策の進め方は？", f"{theme}の典型誤答パターン表を作成し、過去問で反復してください。"),
                ("確認先はどこですか？", "用語集と関連法令を参照してください。"),
            ],
        ))
    return cmp_rows, num_rows, mis_rows


def _write_batch(batch: str) -> list[dict]:
    cmp_rows, num_rows, mis_rows = _batch(batch)
    header = f'''# -*- coding: utf-8 -*-
"""賃管 知識ハブ {batch} 追加分（各10件・計30件）."""

from tools.write_chintai_hub_s30 import _OFFICIAL, cmp, mis, num

L, M, S, P, E = "賃貸住宅管理業法", "民法", "借地借家法", "管理実務", "賃貸経営・PM/AM"

'''
    out = TOOLS / f"write_chintai_hub_{batch.lower()}_content.py"
    parts = [header, "COMPARISONS_ADD = [\n"]
    parts += [emit_cmp(fix_entry(c)) for c in cmp_rows]
    parts += ["]\n\nNUMBERS_ADD = [\n"]
    parts += [emit_num(fix_entry(n)) for n in num_rows]
    parts += ["]\n\nMISTAKES_ADD = [\n"]
    parts += [emit_mis(fix_entry(m)) for m in mis_rows]
    parts.append("]\n")
    out.write_text("".join(parts), encoding="utf-8")
    print("wrote", out)
    return cmp_rows + num_rows + mis_rows


def _premium_block(rows: list[dict]) -> str:
    lines = ["    # --- S35-S39 premium FAQs ---"]
    for row in rows:
        slug = row["slug"]
        title = row["title"]
        summary = row.get("summary", title)
        lines.append(f'    "{slug}": [')
        qs = [
            (f"{title}の要点は？", f"{summary}主体・手続・数値を表で整理してください。" + _OFFICIAL_TAIL),
            (f"{title}の試験引っかけは？", f"{title}では主体逆転・手続省略・数値混同の肢に注意し、用語集と条文で確認してください。" + _OFFICIAL_TAIL),
            (f"{title}の対策は？", f"{title}の比較表・数値表・誤答パターン表を作成し、過去問を反復してください。" + _OFFICIAL_TAIL),
            (f"{title}の確認先は？", "用語集と賃貸住宅管理業法・借地借家法・協議会要項を参照してください。" + _OFFICIAL_TAIL),
        ]
        for q, a in qs:
            lines.append("        (")
            lines.append(f'            "{q}",')
            lines.append(f'            "{a}",')
            lines.append("        ),")
        lines.append("    ],")
    return "\n".join(lines)


def _patch_premium_faqs(all_rows: list[dict]) -> None:
    path = TOOLS / "write_chintai_hub_premium_faqs.py"
    text = path.read_text(encoding="utf-8")
    slugs = {r["slug"] for r in all_rows}
    for slug in slugs:
        text = re.sub(rf'\s*"{re.escape(slug)}": \[[\s\S]*?\],', "", text)
    block = _premium_block(all_rows)
    marker = "\n}\n\n\ndef apply_premium_faqs"
    if marker not in text:
        raise ValueError("PREMIUM_FAQS closing marker not found")
    text = text.replace(marker, f"\n{block}\n}}\n\n\ndef apply_premium_faqs", 1)
    path.write_text(text, encoding="utf-8")
    print("patched premium faqs", len(slugs), "slugs")


def main() -> None:
    rows: list[dict] = []
    for batch in ("S35", "S36", "S37", "S38", "S39"):
        rows += _write_batch(batch)
    _patch_premium_faqs(rows)


if __name__ == "__main__":
    main()
