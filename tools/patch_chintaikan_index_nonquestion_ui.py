#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""index.html の「問題本文・選択肢・CSV過去問」以外の表示文言を賃管向けに整える。"""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"


def main() -> int:
    if not INDEX.is_file():
        print(f"index.html がありません: {INDEX}", file=sys.stderr)
        return 1
    s = INDEX.read_text(encoding="utf-8")

    # --- 構造化データ（FAQ）デモの条文名誤り ---
    s = s.replace("（労働衛生関係法令38条）", "（宅地建物取引業法38条）")
    s = s.replace("（労働衛生関係法令39条2項）", "（宅地建物取引業法39条2項）")
    s = s.replace("（労働衛生関係法令64条の8）", "（宅地建物取引業法64条の8）")
    s = s.replace("（労働衛生関係法令27条）", "（宅地建物取引業法27条）")

    # --- 用語タブ静的抜粋（SEO / noscript 用）---
    old_glos = """<div class="glos-cat-section" data-cat="lawH">
<h3 class="glos-cat-heading">関係法令（有害業務）</h3>
<article class="glos-static-card" itemscope itemtype="https://schema.org/DefinedTerm">
  <h4 class="glos-static-term" itemprop="name">有機溶剤中毒予防規則</h4>
  <p class="glos-static-desc" itemprop="description">有機溶剤の区分（特別・第1種・第2種）に応じて、局所排気装置の設置・作業環境評価・作業主任者の選任などの義務が定められます。試験では区分と措置の対応が頻出です。</p>
</article>
</div>
<div class="glos-cat-section" data-cat="lawN">
<h3 class="glos-cat-heading">関係法令（有害以外）</h3>
<article class="glos-static-card" itemscope itemtype="https://schema.org/DefinedTerm">
  <h4 class="glos-static-term" itemprop="name">衛生管理者</h4>
  <p class="glos-static-desc" itemprop="description">事業者が選任する、労働衛生の専門的管理者です。規模・業種に応じた人数・常勤・専任・資格区分（第一種／第二種など）が試験の定番論点です。</p>
</article>
</div>
<div class="glos-cat-section" data-cat="rightsH">
<h3 class="glos-cat-heading">労働衛生（有害業務）</h3>
<article class="glos-static-card" itemscope itemtype="https://schema.org/DefinedTerm">
  <h4 class="glos-static-term" itemprop="name">局所排気装置</h4>
  <p class="glos-static-desc" itemprop="description">有害物の発生源付近で汚染空気を捕集しダクトで排出する装置です。希釈換気との優先順位や制気速度などが頻出です。</p>
</article>
</div>
<div class="glos-cat-section" data-cat="rightsN">
<h3 class="glos-cat-heading">労働衛生（有害以外）</h3>
<article class="glos-static-card" itemscope itemtype="https://schema.org/DefinedTerm">
  <h4 class="glos-static-term" itemprop="name">WBGT</h4>
  <p class="glos-static-desc" itemprop="description">暑熱環境での温熱負荷を表す指標です。気温・湿度・輻射熱などを総合して評価し、熱中症対策や休憩設計に用います。</p>
</article>
</div>
<div class="glos-cat-section" data-cat="limit">
<h3 class="glos-cat-heading">労働生理</h3>
<article class="glos-static-card" itemscope itemtype="https://schema.org/DefinedTerm">
  <h4 class="glos-static-term" itemprop="name">じん肺</h4>
  <p class="glos-static-desc" itemprop="description">長期の粉じんばく露による肺の線維化疾患です。病理・管理区分・医学的判断がセットで問われます。</p>
</article>
<article class="glos-static-card" itemscope itemtype="https://schema.org/DefinedTerm">
  <h4 class="glos-static-term" itemprop="name">酸素欠乏症</h4>
  <p class="glos-static-desc" itemprop="description">空気中酸素の不足により起きる障害です。窒息ガスとの鑑別や、中枢・循環症状の理解が試験では重要です。</p>
</article>
</div>"""

    new_glos = """<div class="glos-cat-section" data-cat="lawH">
<h3 class="glos-cat-heading">賃貸住宅管理業法等</h3>
<article class="glos-static-card" itemscope itemtype="https://schema.org/DefinedTerm">
  <h4 class="glos-static-term" itemprop="name">管理業務</h4>
  <p class="glos-static-desc" itemprop="description">賃貸住宅の維持保全と家賃等の金銭管理を併せて行う業務。いずれか一方だけでは賃貸住宅管理業法上の管理業務に該当しない点が頻出です。</p>
</article>
</div>
<div class="glos-cat-section" data-cat="lawN">
<h3 class="glos-cat-heading">関連法令</h3>
<article class="glos-static-card" itemscope itemtype="https://schema.org/DefinedTerm">
  <h4 class="glos-static-term" itemprop="name">区分所有法</h4>
  <p class="glos-static-desc" itemprop="description">区分所有建物の管理・使用・規約・集会・決議等を定める法律。賃貸管理では管理組合・共用部分・修繕積立金とセットで論点になります。</p>
</article>
</div>
<div class="glos-cat-section" data-cat="rightsH">
<h3 class="glos-cat-heading">賃貸借・民法・原状回復</h3>
<article class="glos-static-card" itemscope itemtype="https://schema.org/DefinedTerm">
  <h4 class="glos-static-term" itemprop="name">原状回復</h4>
  <p class="glos-static-desc" itemprop="description">賃借人の責めに帰すべき事由による損耗・汚損等を修復すること。経年劣化との線引きや負担範囲が試験の定番です。</p>
</article>
</div>
<div class="glos-cat-section" data-cat="rightsN">
<h3 class="glos-cat-heading">管理実務・書面</h3>
<article class="glos-static-card" itemscope itemtype="https://schema.org/DefinedTerm">
  <h4 class="glos-static-term" itemprop="name">管理受託契約重要事項説明</h4>
  <p class="glos-static-desc" itemprop="description">管理受託契約の締結前に、管理業者が貸主に書面を交付して行う説明。IT重説の要件（双方向性・事前交付・承諾）もセットで押さえます。</p>
</article>
</div>
<div class="glos-cat-section" data-cat="limit">
<h3 class="glos-cat-heading">建築・設備・会計税務</h3>
<article class="glos-static-card" itemscope itemtype="https://schema.org/DefinedTerm">
  <h4 class="glos-static-term" itemprop="name">建築基準法</h4>
  <p class="glos-static-desc" itemprop="description">建築物の位置・構造・設備・用途等の最低基準を定める法律。賃貸住宅管理では内装制限・防火・避難・バリアフリー等が論点になります。</p>
</article>
<article class="glos-static-card" itemscope itemtype="https://schema.org/DefinedTerm">
  <h4 class="glos-static-term" itemprop="name">修繕積立金</h4>
  <p class="glos-static-desc" itemprop="description">区分所有建物の大規模修繕等に備えて管理組合が積み立てる金銭。計上・引当・修繕タイミングとあわせて理解します。</p>
</article>
</div>"""

    if old_glos in s:
        s = s.replace(old_glos, new_glos)
    else:
        print("WARN: 静的用語ブロックの置換スキップ（既に変更済みまたは不一致）", file=sys.stderr)

    # --- CSV 用語カテゴリ列（日本語）→ 内部 cat コード ---
    old_cat_map = """  const catJaToCode = {
    '関係法令（有害業務）': 'lawH',
    '労働衛生（有害業務）': 'rightsH',
    '関係法令（有害以外）': 'lawN',
    '労働衛生（有害以外）': 'rightsN',
    '労働生理': 'limit'
  };"""

    new_cat_map = """  const catJaToCode = {
    '関係法令（有害業務）': 'lawH',
    '労働衛生（有害業務）': 'rightsH',
    '関係法令（有害以外）': 'lawN',
    '労働衛生（有害以外）': 'rightsN',
    '労働生理': 'limit',
    '賃貸住宅管理業法': 'lawH',
    '関連法令': 'lawN',
    '賃貸借契約': 'rightsH',
    '民法': 'rightsH',
    '借地借家法': 'rightsH',
    '原状回復': 'rightsH',
    '管理実務': 'rightsN',
    '建物・設備': 'limit',
    '会計・税務・保険': 'limit',
    '賃貸経営・PM/AM': 'limit'
  };"""

    if old_cat_map in s:
        s = s.replace(old_cat_map, new_cat_map)
    else:
        print("WARN: catJaToCode の置換スキップ", file=sys.stderr)

    # --- 用語タブのチップ表示 ---
    s = s.replace(
        """    const cats = [
      {id:'all',label:'すべて',title:'すべて'},
      {id:'lawH',label:'法令・有害',title:'関係法令（有害業務）'},
      {id:'lawN',label:'法令・有害外',title:'関係法令（有害以外）'},
      {id:'rightsH',label:'衛生・有害',title:'労働衛生（有害業務）'},
      {id:'rightsN',label:'衛生・有害外',title:'労働衛生（有害以外）'},
      {id:'limit',label:'設備等',title:'設備・税務・その他'},
    ];""",
        """    const cats = [
      {id:'all',label:'すべて',title:'すべて'},
      {id:'lawH',label:'業法等',title:'賃貸住宅管理業法等'},
      {id:'lawN',label:'関連法令',title:'関連法令（区分所有法等）'},
      {id:'rightsH',label:'契約・修法',title:'賃貸借・民法・借地借家・原状回復'},
      {id:'rightsN',label:'管理実務',title:'管理受託・書面・報告等'},
      {id:'limit',label:'設備等',title:'建築・設備・会計税務・経営'},
    ];""",
    )

    s = s.replace(
        """  const catNames = {
    lawH: '関係法令（有害業務）',
    rightsH: '労働衛生（有害業務）',
    lawN: '関係法令（有害以外）',
    rightsN: '労働衛生（有害以外）',
    limit: '設備・税務・その他'
  };""",
        """  const catNames = {
    lawH: '賃貸住宅管理業法等',
    rightsH: '賃貸借・民法・原状回復等',
    lawN: '関連法令',
    rightsN: '管理実務・書面等',
    limit: '建築・設備・会計税務等'
  };""",
    )

    s = s.replace(
        "<strong>用語データ（eisei1-data-glossary.js）が読み込めていません。</strong>",
        "<strong>用語データ（埋め込み用語ファイル）が読み込めていません。</strong>",
    )
    s = s.replace(
        "用語カードの表示でエラーが発生しました。<code>eisei1-data-glossary.js</code> の読み込みと、",
        "用語カードの表示でエラーが発生しました。用語データの読み込みと、",
    )

    # --- バッジ（分野マスター）---
    s = s.replace(
        "  {id:'rights_master',  icon:'book',     name:'労働衛生 得意',     desc:'労働衛生10問以上・正答率70%以上'},\n"
        "  {id:'law_master',     icon:'book',     name:'関係法令 得意',     desc:'関係法令10問以上・正答率70%以上'},\n"
        "  {id:'limit_master',   icon:'book',     name:'労働生理 得意',     desc:'労働生理10問以上・正答率70%以上'},",
        "  {id:'rights_master',  icon:'book',     name:'契約・実務 得意',     desc:'契約・実務10問以上・正答率70%以上'},\n"
        "  {id:'law_master',     icon:'book',     name:'賃管法令 得意',     desc:'賃管法令10問以上・正答率70%以上'},\n"
        "  {id:'limit_master',   icon:'book',     name:'設備等 得意',     desc:'設備・税務等10問以上・正答率70%以上'},",
    )

    # --- デイリーミッション ---
    s = s.replace(
        "  // カテゴリC: 分野系（労働衛生・関係法令）\n"
        "  C: [\n"
        "    {id:'rights1',  text:'労働衛生を1問解こう',   type:'field', field:'rights', target:1},\n"
        "    {id:'rights2',  text:'労働衛生を2問解こう',   type:'field', field:'rights', target:2},\n"
        "    {id:'rights3',  text:'労働衛生を3問解こう',   type:'field', field:'rights', target:3},\n"
        "    {id:'rights4',  text:'労働衛生を4問解こう',   type:'field', field:'rights', target:4},\n"
        "    {id:'law1',     text:'関係法令を1問解こう',   type:'field', field:'law',    target:1},\n"
        "    {id:'law2',     text:'関係法令を2問解こう',   type:'field', field:'law',    target:2},\n"
        "    {id:'law3',     text:'関係法令を3問解こう',   type:'field', field:'law',    target:3},\n"
        "    {id:'law4',     text:'関係法令を4問解こう',   type:'field', field:'law',    target:4},",
        "  // カテゴリC: 分野系（賃管法令・契約実務）\n"
        "  C: [\n"
        "    {id:'rights1',  text:'契約・実務を1問解こう',   type:'field', field:'rights', target:1},\n"
        "    {id:'rights2',  text:'契約・実務を2問解こう',   type:'field', field:'rights', target:2},\n"
        "    {id:'rights3',  text:'契約・実務を3問解こう',   type:'field', field:'rights', target:3},\n"
        "    {id:'rights4',  text:'契約・実務を4問解こう',   type:'field', field:'rights', target:4},\n"
        "    {id:'law1',     text:'賃管法令を1問解こう',   type:'field', field:'law',    target:1},\n"
        "    {id:'law2',     text:'賃管法令を2問解こう',   type:'field', field:'law',    target:2},\n"
        "    {id:'law3',     text:'賃管法令を3問解こう',   type:'field', field:'law',    target:3},\n"
        "    {id:'law4',     text:'賃管法令を4問解こう',   type:'field', field:'law',    target:4},",
    )
    s = s.replace(
        "  // カテゴリD: 分野系（労働生理・復習）\n"
        "  D: [\n"
        "    {id:'limit1',   text:'労働生理を1問解こう',      type:'field', field:'limit', target:1},\n"
        "    {id:'limit2',   text:'労働生理を2問解こう',      type:'field', field:'limit', target:2},\n"
        "    {id:'limit3',   text:'労働生理を3問解こう',       type:'field', field:'limit', target:3},\n"
        "    {id:'limit4',   text:'労働生理を4問解こう',      type:'field', field:'limit', target:4},",
        "  // カテゴリD: 分野系（設備等・復習）\n"
        "  D: [\n"
        "    {id:'limit1',   text:'設備・税務等を1問解こう',      type:'field', field:'limit', target:1},\n"
        "    {id:'limit2',   text:'設備・税務等を2問解こう',      type:'field', field:'limit', target:2},\n"
        "    {id:'limit3',   text:'設備・税務等を3問解こう',       type:'field', field:'limit', target:3},\n"
        "    {id:'limit4',   text:'設備・税務等を4問解こう',      type:'field', field:'limit', target:4},",
    )

    # --- オリジナル演習の単元チップ（デモ）---
    old_units = """const ORIG_UNITS = {
  rights:[
    {id:'g_routai',label:'健康障害・作業管理の考え方'},
    {id:'g_workenv',label:'作業環境管理の体系'},
    {id:'g_noise',label:'騒音・振動'},
    {id:'g_heat',label:'暑熱・寒冷'},
    {id:'e_indoor',label:'換気・空調・給排水'},
    {id:'e_dust',label:'粉じん・じんあい'},
    {id:'e_rad',label:'放射線'},
    {id:'e_met',label:'作業環境測定'},
  ],
  law:[
    {id:'h_rouan',label:'労働安全衛生法の体系'},
    {id:'h_kijun',label:'労働衛生基準則'},
    {id:'h_eiseiti',label:'衛生管理者・委員会'},
    {id:'h_tokkan',label:'化学物質・特化則'},
  ],
  limit:[
    {id:'c_bio',label:'労働生理学'},
    {id:'c_anatomy',label:'人体の解剖生理'},
    {id:'c_chem',label:'衛生化学'},
    {id:'c_phys',label:'衛生物理学'},
  ],
};"""

    new_units = """const ORIG_UNITS = {
  rights:[
    {id:'g_routai',label:'賃貸借の基本（解約・更新）'},
    {id:'g_workenv',label:'原状回復・修繕負担'},
    {id:'g_noise',label:'紛争防止・ADR'},
    {id:'g_heat',label:'サブリース・特定賃貸借'},
    {id:'e_indoor',label:'重要事項説明・書面'},
    {id:'e_dust',label:'敷金・家賃・保証'},
    {id:'e_rad',label:'管理受託契約'},
    {id:'e_met',label:'勧誘・広告規制'},
  ],
  law:[
    {id:'h_rouan',label:'登録義務・業の範囲'},
    {id:'h_kijun',label:'遵守事項・名義貸し禁止'},
    {id:'h_eiseiti',label:'監督処分・報告徴収'},
    {id:'h_tokkan',label:'旧登録制度・経過措置'},
  ],
  limit:[
    {id:'c_bio',label:'建築基準法（防火・避難）'},
    {id:'c_anatomy',label:'設備検査・消防'},
    {id:'c_chem',label:'会計・税務の基礎'},
    {id:'c_phys',label:'PM/AM・賃貸経営'},
  ],
};"""

    if old_units in s:
        s = s.replace(old_units, new_units)
    else:
        print("WARN: ORIG_UNITS の置換スキップ", file=sys.stderr)

    # --- コーチカード ---
    s = s.replace(
        "      body:'労働衛生関係法令は出題が厚く得点の土台になりやすいですので、今日は業法を多めに触れ、自信の柱を一緒に太らせていきましょう。'",
        "      body:'賃貸住宅管理業法は出題の柱になりやすいですので、今日は業法と遵守事項を多めに触れ、得点の土台を一緒に太らせていきましょう。'",
    )

    # --- デモログイン ---
    s = s.replace("const email='demo@eisei1.example'", "const email='demo@chintaikan.example'")

    # --- 共有画像ファイル名 ---
    s = s.replace(
        "const fname = `eisei1-master-${now.getFullYear()}${String(now.getMonth()+1).padStart(2,'0')}${String(now.getDate()).padStart(2,'0')}.png`;",
        "const fname = `chintaikan-master-${now.getFullYear()}${String(now.getMonth()+1).padStart(2,'0')}${String(now.getDate()).padStart(2,'0')}.png`;",
    )
    s = s.replace(
        "const fname=`eisei1-master-levelup-Lv${lu.newLv}-${new Date().toISOString().slice(0,10)}.png`;",
        "const fname=`chintaikan-master-levelup-Lv${lu.newLv}-${new Date().toISOString().slice(0,10)}.png`;",
    )
    s = s.replace(
        "const fname=`eisei1-master-badge-${badge.id}-${now.getFullYear()}${String(now.getMonth()+1).padStart(2,'0')}${String(now.getDate()).padStart(2,'0')}.png`;",
        "const fname=`chintaikan-master-badge-${badge.id}-${now.getFullYear()}${String(now.getMonth()+1).padStart(2,'0')}${String(now.getDate()).padStart(2,'0')}.png`;",
    )

    # --- デイリーメッセージ ---
    s = s.replace(
        "    '労働衛生関係法令、得点源にしてしまおう。',",
        "    '賃貸住宅管理業法、得点の柱にしてしまおう。',",
    )
    s = s.replace(
        "    '労働衛生の問題が解けたとき、ちょっと気持ちいい。',",
        "    '契約実務の問題が解けたとき、ちょっと気持ちいい。',",
    )

    # --- 解説の条文ハイライト（賃管で頻出の法令名を追加）---
    s = s.replace(
        "return t.replace(/（((?:民法|労働衛生関係法令|借地借家法|区分所有法|不動産登記法|都市計画法|建築基準法|農地法|国土利用計画法|土地区画整理法|盛土規制法|租税特別措置法|地方税法|地価公示法)[^）]{1,30}？)）/g,",
        "return t.replace(/（((?:民法|賃貸住宅管理業法|宅地建物取引業法|労働衛生関係法令|借地借家法|区分所有法|不動産登記法|都市計画法|建築基準法|農地法|国土利用計画法|土地区画整理法|盛土規制法|租税特別措置法|地方税法|地価公示法)[^）]{1,30}？)）/g,",
    )
    s = s.replace(
        "return t.replace(/（((?:民法|労働衛生関係法令|借地借家法|区分所有法|不動産登記法|都市計画法|建築基準法|農地法|国土利用計画法|土地区画整理法|盛土規制法|宅造法|租税特別措置法|地方税法|地価公示法|住宅品質確保法|住宅金融支援機構法|住宅瑕疵担保履行法)[^）]{1,30}？)）/g,",
        "return t.replace(/（((?:民法|賃貸住宅管理業法|宅地建物取引業法|労働衛生関係法令|借地借家法|区分所有法|不動産登記法|都市計画法|建築基準法|農地法|国土利用計画法|土地区画整理法|盛土規制法|宅造法|租税特別措置法|地方税法|地価公示法|住宅品質確保法|住宅金融支援機構法|住宅瑕疵担保履行法)[^）]{1,30}？)）/g,",
    )

    s = s.replace(
        "console.warn('[glossary] CSV の取得に失敗したため、eisei1-data-glossary.js のデータを使います:",
        "console.warn('[glossary] CSV の取得に失敗したため、埋め込み用語データを使います:",
    )

    INDEX.write_text(s, encoding="utf-8")
    print("Patched non-question UI copy in index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
