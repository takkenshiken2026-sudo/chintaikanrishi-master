#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""eisei1shu の index.html をコピー済みの前提で、賃管マスター向け文言・設定に一括置換する。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"


def main() -> int:
    if not INDEX.is_file():
        print(f"index.html がありません: {INDEX}", file=sys.stderr)
        return 1
    s = INDEX.read_text(encoding="utf-8")

    # 順序に注意（長い文字列から）
    pairs: list[tuple[str, str]] = [
        ("第一種衛生管理者試験", "賃貸不動産経営管理士試験"),
        ("第一種衛生管理者", "賃貸不動産経営管理士"),
        ("一衛マスター", "賃管マスター"),
        ("一衛", "賃管"),
        ("eisei1shu-master.jp", "chintaikanrishi-master.jp"),
        ("eisei1kanri_v1", "chintaikan_master_v1"),
        ("eisei1_mock_bests", "chintaikan_mock_bests"),
        ("eisei1kanri_srs_v1", "chintaikan_master_srs_v1"),
        ("関係法令・労働衛生・労働生理", "賃管法令・契約実務・設備等"),
        ("関係法令5・労働衛生6・労働生理5", "賃管法令5・契約実務6・設備等5"),
        ("data/eisei1_original_questions.csv", "data/past_questions.csv"),
    ]
    for a, b in pairs:
        s = s.replace(a, b)

    # FIELDS（科目名のみ差し替え。id は law/rights/limit のまま互換維持）
    s = re.sub(
        r"var FIELDS = \[[\s\S]*?\];",
        """var FIELDS = [
  { id: 'law', name: '賃管法令・制度' },
  { id: 'rights', name: '契約・実務' },
  { id: 'limit', name: '設備・税務・その他' }
];""",
        s,
        count=1,
    )

    # 用語カードのプレースホルダ補足（CAT_HINT）
    s = s.replace(
        "lawH:'関係法令（有害業務）：粉じん・有機溶剤・特定化学物質・放射線・鉛・酸欠など、特化則と選任・記録の対応づけを整理します。'",
        "lawH:'賃貸住宅管理業法・登録・遵守事項・監督処分など、管理業者の義務と手続を整理します。'",
    )
    s = s.replace(
        "rightsH:'労働衛生（有害業務）：ばく露評価・局所排気・測定・化学物質・放射線・振動騒音など、有害要因の管理を整理します。'",
        "rightsH:'賃貸借・原状回復・サブリース・入居者対応など、契約と実務上の論点を整理します。'",
    )
    s = s.replace(
        "lawN:'関係法令（有害以外）：衛生管理体制・健康診断・教育・委員会・ストレス対応など、共通の法令論点を整理します。'",
        "lawN:'国土交通省令・ガイドライン・関連法令（個人情報・消費者法等）の位置づけを整理します。'",
    )
    s = s.replace(
        "rightsN:'労働衛生（有害以外）：温熱・照明・VDT・エルゴノミクス・感染・一般環境など、広い労働衛生を整理します。'",
        "rightsN:'賃貸借・管理受託・重要事項説明・紛争防止など、契約実務の論点を整理します。'",
    )
    s = s.replace(
        "limit:'労働生理：解剖生理・体内動態・毒性機序・疾患の素地を整理します。'",
        "limit:'建物・設備・会計税務・不動産証券化など、設備と数字の論点を整理します。'",
    )
    s = s.replace(
        "exam:'学習の進め方・肢の読み方。長文は主語（誰の義務か）と数値条件をマークすると速くなります。'",
        "exam:'学習の進め方・肢の読み方。長文は当事者（貸主・借主・管理業者）と数値・期限をマークすると速くなります。'",
    )

    # フッター注記（公式リンク）
    s = s.replace(
        '試験本番の原文・公式解答・試験日程などは<a href="https://www.exam.or.jp/" target="_blank" rel="noopener" style="color:var(--text2);text-decoration:underline">安全衛生技術試験協会の公式サイト</a>を、労働安全衛生に関する法令・通達の原文は<a href="https://www.mhlw.go.jp/" target="_blank" rel="noopener" style="color:var(--text2);text-decoration:underline">厚生労働省</a>のウェブサイトをご確認ください。',
        '試験本番の原文・合格基準・試験日程などは<a href="https://www.chintaikan.or.jp/" target="_blank" rel="noopener" style="color:var(--text2);text-decoration:underline">公益財団法人日本賃貸住宅管理協会</a>等の公式情報を、法令・通達の原文は<a href="https://www.mlit.go.jp/" target="_blank" rel="noopener" style="color:var(--text2);text-decoration:underline">国土交通省</a>等のウェブサイトをご確認ください。',
    )

    # 模擬試験プール年度（CSV の実年度に合わせる）
    s = re.sub(
        r"const MOCK_PATTERNS = \[[\s\S]*?\];",
        """const MOCK_PATTERNS = [
  {id:1, title:'模試 第1回', subtitle:'平成27年度〜令和7年度プールから16問',
   desc:'賃管法令・契約実務・設備等の配分に沿ってランダム抽出します。',
   years:[2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025]},
  {id:2, title:'模試 第2回', subtitle:'同プールから別構成で16問',
   desc:'同じプールから別シードで再抽選します。',
   years:[2015,2016,2017,2018,2019,2020,2021,2022,2023,2024,2025]},
];""",
        s,
        count=1,
    )

    # 模試画面の科目ラベル（ハードコード解除 → FIELDS 参照）
    old = """document.getElementById('q-meta').innerHTML=`<span class="tag tag-gray">${{law:'関係法令',rights:'労働衛生',limit:'労働生理'}[q.field]}</span><span class="tag tag-blue">模試${mockState.patternId} 問${q.num}</span>`;"""
    new = """document.getElementById('q-meta').innerHTML=`<span class="tag tag-gray">${(FIELDS.find(f=>f.id===q.field)||{name:'—'}).name}</span><span class="tag tag-blue">模試${mockState.patternId} 問${q.num}</span>`;"""
    if old not in s:
        # 既に置換済みの再実行に備え、部分一致でスキップ
        if "模試${mockState.patternId}" in s and "{law:'関係法令'" not in s:
            pass
        else:
            print("WARN: mock q-meta template not found; check index.html", file=sys.stderr)
    else:
        s = s.replace(old, new)

    INDEX.write_text(s, encoding="utf-8")
    print(f"Patched {INDEX}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
