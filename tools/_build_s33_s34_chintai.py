#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Generate write_chintai_hub_s33/s34_content.py and premium FAQ block."""

from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOLS = Path(__file__).resolve().parent

from _hub_content_emit import emit_cmp, emit_mis, emit_num, fix_entry, qa4  # noqa: E402

with (ROOT / "data/glossary_terms.csv").open(encoding="utf-8-sig") as _f:
    GLOSS = {r["term"] for r in csv.DictReader(_f)}


def _rel(*terms: str) -> str:
    ok = [t for t in terms if t in GLOSS]
    for d in ("借地借家法", "敷金", "更新料", "普通借家", "賃貸不動産経営管理士", "管理受託契約", "火災保険"):
        if len(ok) >= 2:
            break
        if d in GLOSS and d not in ok:
            ok.append(d)
    return ";".join(ok[:3])


def _t(title: str, batch: str) -> str:
    return title


_OFFICIAL_TAIL = (
    "賃管試験では用語集と条文の対応づけが得点の鍵になります。"
    "最新の試験要項もあわせて確認してください。"
)


def _faq(qa: list[tuple[str, str]]) -> list[tuple[str, str]]:
    out = []
    for q, a in qa:
        if len(a) < 100:
            a = a + _OFFICIAL_TAIL
        out.append((q, a))
    return out


def _cmp(slug, title, cat, t1, t2, summary, lead, points, mistakes, tip, rel, qa):
    return {
        "slug": slug,
        "title": title,
        "cat": cat,
        "tags": f"{t1};{t2}",
        "summary": summary,
        "labels": f"{t1};{t2}",
        "axes": [
            ("主体", [f"{t1}の論点", f"{t2}の論点"]),
            ("目的", ["試験頻出", "実務連動"]),
            ("手続", ["書面・説明", "契約・届出"]),
            ("試験", [f"「{t1}＝{t2}」", "「同一制度」"]),
            ("混同", ["主体逆転", "法令取違え"]),
        ],
        "article_title": f"{title}｜賃貸不動産経営管理士",
        "lead": lead,
        "points": points,
        "mistakes": mistakes,
        "tip": tip,
        "related": rel,
        "qa": _faq(qa),
    }


def _num(slug, title, cat, tag, summary, highlight, lead, points, mistakes, tip, rel, qa):
    return {
        "slug": slug,
        "title": title,
        "cat": cat,
        "tags": tag,
        "summary": summary,
        "highlight": highlight,
        "items": [
            ("数値", highlight.split("（")[0], "試験頻出"),
            ("根拠", "法令・要項", "条文確認"),
            ("対象", tag.split(";")[0], "適用範囲"),
            ("試験", "混同肢", "正誤確認"),
            ("確認", "用語集", "最新要項"),
        ],
        "article_title": f"{title}｜数値早見",
        "lead": lead,
        "points": points,
        "mistakes": mistakes,
        "tip": tip,
        "related": rel,
        "qa": _faq(qa),
    }


def _mis(slug, title, cat, t1, t2, summary, lead, points, mistakes, tip, rel, qa):
    return {
        "slug": slug,
        "title": title,
        "cat": cat,
        "tags": f"{t1};{t2}",
        "summary": summary,
        "confusion": f"{t1}と{t2}の混同。",
        "patterns": [
            ("主体", "逆転", "正しい主体", "主体誤"),
            ("手続", "省略", "法定手続", "手続誤"),
            ("数値", "固定誤", "条文確認", "数値誤"),
            ("効果", "同一", "別制度", "効果誤"),
        ],
        "article_title": f"{title}｜賃貸不動産経営管理士",
        "lead": lead,
        "points": points,
        "mistakes": mistakes,
        "tip": tip,
        "related": rel,
        "qa": _faq(qa),
    }


def _batch(batch: str, topics: dict) -> tuple[list, list, list]:
    sfx = f"-{batch.lower()}"
    cmp_rows, num_rows, mis_rows = [], [], []
    for i, (slug_base, title, cat, t1, t2, summary) in enumerate(topics["compare"], 1):
        title = _t(title, batch)
        cmp_rows.append(
            _cmp(
                f"{slug_base}{sfx}",
                title,
                cat,
                t1,
                t2,
                summary,
                f"{summary}主体・手続・数値を表で整理し、過去問の言い換え肢に対応できるようにしてください。",
                f"{t1}と{t2}を分離;主体確認;書面・届出;試験の正誤肢に注意",
                f"{t1}＝{t2};主体逆転;手続省略;試験の正誤肢に注意",
                f"「{t1}と{t2}を分ける」。",
                _rel(t1, t2),
                [
                    (f"{t1}の要点は？", f"{summary}{t1}の定義・主体・効果を用語集で確認してください。"),
                    (f"{t2}との違いは？", f"{t2}は別枠の制度です。{t1}と混同しないよう比較表を作成してください。"),
                    ("試験対策の進め方は？", "過去問で主体・手続・数値の三層表を作成し、正誤肢を分類してください。"),
                    ("確認先はどこですか？", "用語集と賃貸住宅管理業法・借地借家法を参照してください。"),
                ],
            )
        )
    for slug_base, title, cat, tag, summary, highlight, rel in topics["numbers"]:
        title = _t(title, batch)
        parts = [p.strip() for p in tag.split(";") if p.strip()]
        num_rows.append(
            _num(
                f"{slug_base}{sfx}",
                title,
                cat,
                tag,
                summary,
                highlight,
                f"{summary}数値は年度・条文で変わる場合があるため、学習中も最新要項で確認してください。",
                f"{highlight};条文確認;混同禁止;用語集参照",
                f"数値固定暗記;条文無視;混同;試験の正誤肢に注意",
                f"「{highlight.split('（')[0]}を確認」。",
                rel or _rel(*parts),
                [
                    ("数値の要点は？", f"{summary}正確な数値は借地借家法・賃管法・試験要項で確認してください。"),
                    ("試験の引っかけは？", "類似制度の数値を当てはめる肢に注意し、制度ごとに色分けしてください。"),
                    ("試験対策の進め方は？", "数値一覧表を作成し、過去問の正誤を反復してください。"),
                    ("確認先はどこですか？", "借地借家法・賃管法・協議会要項を参照してください。"),
                ],
            )
        )
    for slug_base, title, cat, t1, t2, summary in topics["mistakes"]:
        title = _t(title, batch)
        mis_rows.append(
            _mis(
                f"{slug_base}{sfx}",
                title,
                cat,
                t1,
                t2,
                summary,
                f"{summary}正しい整理を表にまとめ、過去問の典型誤答肢を分類してください。",
                f"{t1}≠{t2};主体・手続・数値を分離;用語集参照",
                f"同一視;主体逆転;手続省略;試験の正誤肢に注意",
                f"「{t1}と{t2}は別制度」。",
                _rel(t1, t2),
                [
                    ("誤りの内容は何ですか？", f"{summary}試験では言い換え肢として頻出です。"),
                    ("正しい理解は何ですか？", f"{t1}と{t2}を主体・手続・効果で分けて整理してください。"),
                    ("試験対策の進め方は？", "典型誤答パターン表を作成し、過去問で反復してください。"),
                    ("確認先はどこですか？", "用語集と関連法令を参照してください。"),
                ],
            )
        )
    return cmp_rows, num_rows, mis_rows


S33_TOPICS = {
    "compare": [
        ("nyukyo-shinsa-yoshin", "入居審査と与信調査", "P", "入居審査", "家賃債務保証", "入居審査の基準と家賃債務保証・与信の関係を整理します。"),
        ("genjo-tokuyaku-guide", "原状回復特約とガイドライン", "S", "借主負担特約", "原状回復ガイドライン", "特約と原状回復ガイドラインの関係・通常損耗の整理をします。"),
        ("kanri-renkei-baikai", "管理業務連携と宅建媒介", "L", "管理業務", "媒介契約", "賃管法の管理業務と宅建業の媒介業務の連携・分界を整理します。"),
        ("kasai-hoken-kazai", "火災保険と家財保険", "P", "火災保険", "家賃補償保険", "建物・家財・家賃補償の保険類型と管理実務上の位置づけを整理します。"),
        ("nyukyo-setsumei-jusetsu", "入居者説明と重要事項説明", "L", "管理受託契約重要事項説明", "重要事項説明（宅建業法）", "入居者向け説明と宅建・賃管法上の重要事項説明の違いを整理します。"),
        ("yachin-kaage-koushin", "家賃値上げと更新料", "S", "賃料改定の協議", "更新料", "賃料改定・値上げ協議と合意更新の更新料上限を整理します。"),
        ("meiwatashi-sosho", "明渡訴訟と立退料", "S", "明渡し訴訟", "立退料", "明渡し訴訟の手続と更新拒絶時の立退料の関係を整理します。"),
        ("sublease-hanrei", "サブリース判例とガイドライン", "E", "サブリース判例（最高裁平成15.10.21判決等）", "サブリースガイドライン", "判例・ガイドライン・特定賃貸借の整理をします。"),
        ("pm-am-kanri", "PMとAMの役割", "E", "プロパティマネジメント（PM）", "アセットマネジメント（AM）", "現場運営と資産戦略の役割分担を整理します。"),
        ("teiki-futsu-hikaku", "定期借家と普通借家（S33）", "S", "定期建物賃貸借契約", "普通建物賃貸借契約", "満了終了と更新制度の違いを再整理します。"),
    ],
    "numbers": [
        ("koushin-moushiire-kikan", "更新申入期間", "S", "更新申入;普通借家", "更新申入の期間（1年〜6ヶ月前等）を整理します。", "1年〜6ヶ月前（普通借家・目安）", "普通借家;合意更新;借地借家法"),
        ("shikikin-jogen-2bai", "敷金上限2倍", "S", "敷金;借地借家法", "居住用建物の敷金上限（家賃2倍以内）を整理します。", "家賃の2倍以内（居住用・目安）", "敷金;借地借家法;普通借家"),
        ("koushinryo-1getsu", "合意更新の更新料", "S", "更新料;合意更新", "合意更新における更新料上限を整理します。", "1ヶ月分以内（建物・合意更新）", "更新料;合意更新;借地借家法"),
        ("ritai-6getsu", "立退料6ヶ月上限", "S", "立退料;更新拒絶通知", "更新拒絶時の立退料上限を整理します。", "6ヶ月分以内（建物・目安）", "立退料;更新料;借地借家法"),
        ("taiin-yokoku-1getsu", "退去予告1ヶ月", "S", "借地借家法;退去立会い", "建物賃貸借の退去予告期間を整理します。", "1ヶ月前予告（建物・目安）", "借地借家法;退去立会い;普通借家"),
        ("shikikin-henkan-1getsu", "敷金返還1ヶ月", "S", "敷金;原状回復費用の精算", "敷金返還期限の目安を整理します。", "1ヶ月以内（契約終了後・目安）", "敷金;原状回復費用の精算;借地借家法"),
        ("teiki-kikan-min", "定期借家の最短期間", "S", "定期借家;定期建物賃貸借契約", "定期借家の期間要件を整理します。", "1年以上（定期・目安）", "定期借家;定期建物賃貸借契約;借地借家法"),
        ("senren-baikai-3getsu", "専任媒介3ヶ月", "E", "専任媒介契約;宅地建物取引士", "専任媒介契約の有効期間上限を整理します。", "3ヶ月を超える定めは無効（目安）", "専任媒介契約;媒介契約;宅地建物取引士"),
        ("chintai-shiken-50mon", "賃管試験50問", "L", "賃貸不動産経営管理士;管理業務", "賃管士試験の出題数を整理します。", "50問（マークシート・要項確認）", "賃貸不動産経営管理士;管理業務;管理受託契約"),
        ("hoken-tekiyo-kikan", "火災保険の適用期間", "P", "火災保険;管理受託契約", "火災保険の契約期間・更新の目安を整理します。", "1年契約・更新（実務目安）", "火災保険;管理受託契約;借地借家法"),
    ],
    "mistakes": [
        ("shinsa-hosho-same", "入居審査と保証を同一視する誤り", "P", "入居審査", "家賃債務保証", "審査基準と保証契約・登録制度を同一とみなす誤り。"),
        ("tokuyaku-gensho-same", "原状回復特約と修繕を同一視する誤り", "S", "借主負担特約", "原状回復", "特約で借主負担を拡大し貸主修繕まで含める誤り。"),
        ("kanri-baikai-same", "管理受託と媒介を同一視する誤り", "L", "管理受託契約", "媒介契約", "管理業者が宅建媒介を要しない等の混同。"),
        ("hoken-yachin-same", "火災保険と家賃補償を同一視する誤り", "P", "火災保険", "家賃補償保険", "補償対象・契約者・管理実務上の位置づけの混同。"),
        ("jusetsu-it-same", "IT重説と口頭説明を同一視する誤り", "L", "IT重説", "重要事項説明（宅建業法）", "事前書面交付・承諾要件を無視する誤り。"),
        ("kaage-koushin-same", "家賃値上げと更新料を同一視する誤り", "S", "賃料改定の協議", "更新料", "改定協議と合意更新の更新料を混同する誤り。"),
        ("sosho-ritai-same", "明渡訴訟と立退料を同一視する誤り", "S", "明渡し訴訟", "立退料", "訴訟手続と更新拒絶時の立退料支払を混同する誤り。"),
        ("sublease-kanri-same", "サブリースと管理受託を同一視する誤り", "E", "サブリーススキーム", "管理受託契約", "一括借上転貸と委託管理の契約類型混同。"),
        ("pm-am-same", "PMとAMを同一視する誤り", "E", "プロパティマネジメント（PM）", "アセットマネジメント（AM）", "現場運営と資産戦略の役割逆転。"),
        ("teiki-koshin-same", "定期借家への更新申入適用", "S", "定期建物賃貸借契約", "普通借家", "定期借家に普通借家の更新制度を適用する誤り。"),
    ],
}

S34_TOPICS = {
    "compare": [
        ("nyukyo-check-sheet", "入居時チェックと原状回復", "P", "入居時のチェックシート", "原状回復", "入居時記録と退去時原状回復・敷金精算の連動を整理します。"),
        ("tokuyaku-pet", "ペット特約と民泊禁止", "S", "ペット飼育特約", "民泊禁止特約", "特約の種類と管理受託・募集への影響を整理します。"),
        ("kanri-it-ju", "IT重説と管理受託重説", "L", "IT重説", "管理受託契約重要事項説明", "オンライン説明方式と賃管法上の重説の要件を整理します。"),
        ("hoken-tenant", "借家人賠償と火災保険", "P", "火災保険", "借地借家法", "借主・貸主・管理会社の保険・賠償責任を整理します。"),
        ("nyukyo-gaikokujin", "外国人入居と入居審査", "P", "外国人の入居", "入居審査", "外国人入居時の説明・審査・契約実務を整理します。"),
        ("chintai-chukai", "賃料改定特約と協議", "S", "賃料の改定特約", "賃料改定の協議", "特約排除・協議・値上げの手続を整理します。"),
        ("meiwatashi-yuyo", "明渡猶予と明渡訴訟", "S", "明渡し猶予制度", "明渡し訴訟", "猶予制度と訴訟・執行の関係を整理します。"),
        ("sublease-type", "パススルーと賃料保証型", "E", "パススルー型サブリース", "賃料保証型サブリース", "サブリース類型とリスク配分を整理します。"),
        ("master-sublease", "マスターリース契約とサブリース", "E", "マスターリース契約", "サブリース契約", "原賃貸借と転貸・管理の関係を整理します。"),
        ("jutaku-jigyou-hikaku", "住宅賃貸と事業用賃貸", "M", "借地借家法", "定期借家", "用途別の規制・契約類型の違いを整理します。"),
    ],
    "numbers": [
        ("koshin-kikan-5nen", "登録更新5年", "L", "登録の更新;賃貸不動産経営管理士", "賃管士登録の更新周期を整理します。", "5年ごとに更新（登録・要項確認）", "登録の更新;賃貸不動産経営管理士;業務管理者"),
        ("kikan-teiki-1nen", "短期借家1年", "S", "定期借家;借地借家法", "短期借家の期間上限を整理します。", "1年以下（短期借家・目安）", "定期借家;借地借家法;普通借家"),
        ("hosho-tesuryo", "家賃保証手数料", "P", "家賃債務保証;家賃債務保証会社", "保証料・手数料の実務目安を整理します。", "契約による（敷金返還とは別）", "家賃債務保証;家賃債務保証会社;敷金"),
        ("azukari-betsu", "預り金全額分別", "L", "分別管理義務;敷金", "預り金の全額分別管理を整理します。", "預かった額の全額を分別", "分別管理義務;敷金;管理受託契約"),
        ("genjo-jiko-5nen", "原状回復請求時効", "M", "原状回復;改正民法（2020年4月施行）", "原状回復費用請求の消滅時効目安を整理します。", "短期消滅時効5年（目安）", "原状回復;原状回復費用の精算;改正民法（2020年4月施行）"),
        ("chukai-hoshu", "媒介報酬の目安", "E", "媒介契約;宅地建物取引士", "賃貸媒介報酬の上限・目安を整理します。", "1ヶ月分以内（賃料・目安）", "媒介契約;宅地建物取引士;専任媒介契約"),
        ("tachiai-kigen", "退去立会いの期限", "P", "退去立会い;敷金", "立会いと敷金返還期限の関係を整理します。", "返還1ヶ月・立会は実務推奨", "退去立会い;敷金;原状回復費用の精算"),
        ("it-jusetsu-jizen", "IT重説の事前書面", "L", "IT重説;重要事項説明（宅建業法）", "IT重説の事前書面交付要件を整理します。", "説明前に書面交付・承諾", "IT重説;重要事項説明（宅建業法）;管理受託契約重要事項説明"),
        ("nyukyo-ritsu", "入居率の目安", "E", "入居率;プロパティマネジメント（PM）", "PM指標としての入居率を整理します。", "物件・エリアで異なる（指標）", "入居率;プロパティマネジメント（PM）;管理受託契約"),
        ("sublease-chintai", "サブリース賃料", "E", "サブリース契約;成約家賃", "原賃料・転賃料・成約家賃の関係を整理します。", "原賃料＋転賃料（スキーム次第）", "サブリース契約;成約家賃;マスターリース契約"),
    ],
    "mistakes": [
        ("check-gensho-same", "入居チェックと原状回復を混同する誤り", "P", "入居時のチェックシート", "原状回復", "入居時記録があれば任意控除できる等の誤解。"),
        ("pet-minpaku-same", "ペット特約と民泊禁止を混同する誤り", "S", "ペット飼育特約", "民泊禁止特約", "特約の効果・対象・違反効果の混同。"),
        ("it-jusetsu-same", "IT重説と電磁的重説を混同する誤り", "L", "IT重説", "ITによる重要事項説明", "双方向性・事前書面・承諾要件の混同。"),
        ("hoken-kanri-same", "保険加入を管理会社義務とする誤り", "P", "火災保険", "管理受託契約", "契約者・受益者・説明義務の主体混同。"),
        ("gaikokujin-disc-same", "外国人入居と差別を混同する誤り", "P", "外国人の入居", "入居審査", "正当な審査と不当差別の混同。"),
        ("chintai-tokuyaku-same", "改定特約と更新料を混同する誤り", "S", "賃料の改定特約", "更新料", "値上げ特約と合意更新の更新料の混同。"),
        ("yuyo-sosho-same", "明渡猶予と更新を混同する誤り", "S", "明渡し猶予制度", "合意更新", "猶予期間中の使用と更新制度の混同。"),
        ("sublease-type-same", "サブリース類型を混同する誤り", "E", "パススルー型サブリース", "賃料保証型サブリース", "リスク配分・空室負担の混同。"),
        ("master-kanri-same", "マスターリースと管理受託を混同する誤り", "E", "マスターリース契約", "管理受託契約", "賃貸借と委託の契約類型混同。"),
        ("jutaku-jigyou-same", "住宅と事業用規制を混同する誤り", "S", "借地借家法", "定期借家", "敷金上限等を用途問わず同一とする誤り。"),
    ],
}


def _write_batch(batch: str, topics: dict) -> None:
    cmp_rows, num_rows, mis_rows = _batch(batch, topics)
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
    lines = ['    # --- S33/S34 premium FAQs ---']
    for row in rows:
        slug = row["slug"]
        lines.append(f'    "{slug}": [')
        qs = [
            (f"{row['title']}の要点は？", f"{row.get('summary', row['title'])}主体・手続・数値を表で整理してください。" + _OFFICIAL_TAIL),
            ("試験での引っかけは？", "主体逆転・手続省略・数値混同の肢に注意し、用語集と条文で確認してください。" + _OFFICIAL_TAIL),
            ("試験対策の進め方は？", "比較表・数値表・誤答パターン表を作成し、過去問を反復してください。" + _OFFICIAL_TAIL),
            ("確認先はどこですか？", "用語集と賃貸住宅管理業法・借地借家法・協議会要項を参照してください。" + _OFFICIAL_TAIL),
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
    # remove existing s33/s34 entries if re-run
    for slug in slugs:
        text = re.sub(rf'\s*"{re.escape(slug)}": \[[\s\S]*?\],', "", text)
    block = _premium_block(all_rows)
    marker = "    ],}\n\n\ndef apply_premium_faqs"
    if marker not in text:
        marker = "\n}\n\n\ndef apply_premium_faqs"
    if marker not in text:
        raise ValueError("PREMIUM_FAQS closing marker not found")
    if marker == "    ],}\n\n\ndef apply_premium_faqs":
        text = text.replace(marker, f"    ],\n{block}\n}}\n\n\ndef apply_premium_faqs", 1)
    else:
        text = text.replace(marker, f",\n{block}\n}}\n\n\ndef apply_premium_faqs", 1)
    path.write_text(text, encoding="utf-8")
    print("patched premium faqs", len(slugs), "slugs")


def main() -> None:
    rows = []
    rows += _write_batch("S33", S33_TOPICS)
    rows += _write_batch("S34", S34_TOPICS)
    _patch_premium_faqs(rows)


if __name__ == "__main__":
    main()
