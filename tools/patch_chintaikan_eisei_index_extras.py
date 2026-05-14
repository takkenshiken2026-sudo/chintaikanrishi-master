#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""index.html 内の科目ラベル・メタキーワード等を賃管向けに追加置換する。"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INDEX = ROOT / "index.html"

NEW_DICT = "{law:'賃管法令・制度',rights:'契約・実務',limit:'設備・税務・その他'}"
NEW_DICT_SP = "{law: '賃管法令・制度', rights: '契約・実務', limit: '設備・税務・その他'}"


def main() -> int:
    s = INDEX.read_text(encoding="utf-8")

    s = s.replace(
        '<meta name="keywords" content="賃貸不動産経営管理士,衛生管理者試験,賃貸不動産経営管理士試験,試験演習,過去問無料,模擬試験,関係法令,労働衛生,労働生理,資格学習,合格">',
        '<meta name="keywords" content="賃貸不動産経営管理士,賃管,賃貸住宅管理業法,過去問,模擬試験,用語集,賃貸借,原状回復,サブリース,資格学習,合格">',
    )

    s = s.replace(
        """          <li>関係法令（労働安全衛生法体系・基準則・特化則など）</li>
          <li>労働衛生（作業環境管理・温熱・化学物質・局所排気・測定など）</li>
          <li>労働生理（解剖生理・衛生化・衛生物理・有害因子の作用など）</li>""",
        """          <li>賃管法令（賃貸住宅管理業法・登録・遵守事項・監督処分など）</li>
          <li>契約・実務（賃貸借・原状回復・サブリース・重要事項説明など）</li>
          <li>設備・税務・その他（建築・設備・会計税務・不動産証券化など）</li>""",
    )

    s = s.replace("const FIELD_LABELS = {law:'関係法令', rights:'労働衛生', limit:'労働生理'};", f"const FIELD_LABELS = {NEW_DICT_SP};")
    s = s.replace("const ORIG_FIELD_LABELS = {law:'関係法令', rights:'労働衛生', limit:'労働生理'};", f"const ORIG_FIELD_LABELS = {NEW_DICT_SP};")
    s = s.replace("const fieldNames = {law:'関係法令',rights:'労働衛生',limit:'労働生理'};", f"const fieldNames = {NEW_DICT};")

    s = s.replace(
        "const FIELD_NAMES={law:'関係法令',rights:'労働衛生',limit:'労働生理'};",
        f"const FIELD_NAMES={NEW_DICT};",
    )

    s = s.replace(
        "const SHARE_TWITTER_HASHTAGS = '衛生管理者,賃貸不動産経営管理士,賃管マスター';",
        "const SHARE_TWITTER_HASHTAGS = '賃貸不動産経営管理士,賃管,賃管マスター';",
    )

    # 一問一答の科目チップ
    s = s.replace(
        '<button type="button" class="chip" data-field="rights" onclick="selectIchiField(this)">労働衛生</button>',
        '<button type="button" class="chip" data-field="rights" onclick="selectIchiField(this)">契約・実務</button>',
    )
    s = s.replace(
        '<button type="button" class="chip" data-field="law" onclick="selectIchiField(this)">関係法令</button>',
        '<button type="button" class="chip" data-field="law" onclick="selectIchiField(this)">賃管法令・制度</button>',
    )
    s = s.replace(
        '<button type="button" class="chip" data-field="limit" onclick="selectIchiField(this)">労働生理</button>',
        '<button type="button" class="chip" data-field="limit" onclick="selectIchiField(this)">設備・税務・その他</button>',
    )

    # 用語カテゴリ UI（見出し短名）
    s = s.replace("{id:'limit',label:'労働生理',title:'労働生理'}", "{id:'limit',label:'設備等',title:'設備・税務・その他'}")
    s = s.replace("limit: '労働生理'", "limit: '設備・税務・その他'")

    INDEX.write_text(s, encoding="utf-8")
    print("Patched field labels and keywords in index.html")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
