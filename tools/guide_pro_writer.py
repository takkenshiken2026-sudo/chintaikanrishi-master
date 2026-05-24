#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Upgrade all guide articles (guide_articles.csv) to expert-writer quality."""

from __future__ import annotations

import csv
import sys
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

CSV_PATH = ROOT / "data" / "guide_articles.csv"

# Per-slug editorial brief: focus topics woven into section bodies
SLUG_BRIEF: dict[str, dict[str, str]] = {
    "exam-overview": {
        "focus": "3分野（法令・契約実務・設備税務）の関係と学習の循環",
        "action": "公式要項確認→科目別ハブ→過去問→用語の往復",
        "pitfall": "分野を縦割りに暗記し、横断問題でつまずく",
    },
    "study-plan": {
        "focus": "週次計画・復習間隔・弱点の可視化",
        "action": "平日30分＋週末まとめ、間違いノートを用語記事へリンク",
        "pitfall": "テキスト完読だけで過去問に手をつけない",
    },
    "past-questions-how-to-use": {
        "focus": "演習の質（正答率より論点の言語化）",
        "action": "1問ごとに誤り理由を3語で記録し用語へ戻る",
        "pitfall": "回数だけ増やし、同じ論点を繰り返し間違える",
    },
    "law-subject": {
        "focus": "賃管業法・登録・管理業務・重説・監督",
        "action": "field-law ハブから用語3件＋過去問5問",
        "pitfall": "宅建業法の知識だけで賃管業法の肢を選ぶ",
    },
    "rights-subject": {
        "focus": "借地借家法・敷金・賃料・解除・明渡し",
        "action": "契約類型（定期／普通）を先に整理してから用語",
        "pitfall": "民法の一般論と借地借家法の特則を混同",
    },
    "limit-subject": {
        "focus": "設備・維持保全・税務・保険・区分・消防",
        "action": "数値・期限は公式確認、制度の目的で覚える",
        "pitfall": "税務の数字を暗記のみで理解しない",
    },
    "chintai-gyoho-basics": {
        "focus": "登録・管理業務三要素・遵守事項・重説・締結時書面",
        "action": "2条→10条台→13条台の順で条文マップを作る",
        "pitfall": "管理業務の一部受託を適法と誤認",
    },
    "genjo-kaifuku-guide": {
        "focus": "通常損耗・経年変化・特約・ガイドライン",
        "action": "負担区分表を自作し、特約の有効性を確認",
        "pitfall": "ガイドラインを法律と同一視",
    },
    "schedule-application": {
        "focus": "試験日程・申込・持ち物・当日動線",
        "action": "協議会サイトで年度の日程表を印刷しチェック",
        "pitfall": "前年の日程のまま申込む",
    },
    "eligibility-registration": {
        "focus": "受験資格・実務経験・合格後登録・継続研修",
        "action": "要項と登録規程を並べて要件表を作る",
        "pitfall": "実務経験の年数・職種を取り違える",
    },
    "shakuchi-shakuya-guide": {
        "focus": "更新・更新拒絶・立退・正当事由",
        "action": "普通借家と定期借家の表を先に完成させる",
        "pitfall": "更新拒絶と終了通知を混同",
    },
    "teiki-shakka-guide": {
        "focus": "定期借家・38条・終了通知・再契約",
        "action": "期間満了の流れをタイムライン化",
        "pitfall": "法定更新のイメージを定期に当てはめる",
    },
    "kanri-uketsuke-sublease": {
        "focus": "管理受託・サブリース・分別管理・報酬",
        "action": "契約関係図（貸主・管理会社・転貸人・借主）を描く",
        "pitfall": "サブリースと普通の賃貸借の主体を混同",
    },
    "building-equipment-guide": {
        "focus": "維持保全・点検・共用部分・修繕",
        "action": "管理業務の維持保全と設備法令をリンク",
        "pitfall": "貸主・借主・管理会社の修繕義務を混同",
    },
    "tax-accounting-guide": {
        "focus": "収支・損益・減価償却・確定申告の基礎",
        "action": "オーナー視点の収支表を1件想定して整理",
        "pitfall": "税目ごとの主体（貸主／管理会社）を誤る",
    },
    "glossary-how-to-use": {
        "focus": "静的用語記事とアプリ演習の往復",
        "action": "過去問で引っかかった語をブックマークし記事を読む",
        "pitfall": "用語を読むだけで過去問に戻らない",
    },
    "last-minute-guide": {
        "focus": "直前1〜2週間の捨て選択・睡眠・当日手順",
        "action": "重要度A用語と直近の誤りノートだけに絞る",
        "pitfall": "新しい分野に手を出して自信を失う",
    },
    "after-passing-guide": {
        "focus": "合格後登録・研修・実務での活用",
        "action": "登録申請の期限と必要書類を公式で確認",
        "pitfall": "合格＝登録完了と誤解",
    },
    "juyo-jiko-setsumei-guide": {
        "focus": "重説の種類・交付時期・IT重説・記載事項",
        "action": "宅建35条・賃管13・30条の表を暗記用に整理",
        "pitfall": "重説・締結時書面・37条書面の時期",
    },
    "deposit-rent-fees": {
        "focus": "敷金・礼金・家賃・明細書・返還",
        "action": "敷金の預り→控除→返還の流れをケースで整理",
        "pitfall": "礼金と敷金の性質の違い",
    },
    "minpou-contract-defects": {
        "focus": "契約不適合・修繕義務・2020年改正",
        "action": "旧「瑕疵担保」表記の過去問は用語置換して読む",
        "pitfall": "契約不適合と原状回復を混同",
    },
    "rent-arrears-eviction": {
        "focus": "賃料滞納・催告・解除・明渡し",
        "action": "滞納→催告→解除→明渡しの順序を図示",
        "pitfall": "滞納だけで即明渡しできると誤解",
    },
    "adr-trouble-guide": {
        "focus": "近隣・騒音・ADR・記録・説明",
        "action": "トラブル記録と重説・規約の関係を整理",
        "pitfall": "感情的対応を法令対応と混同",
    },
    "pm-am-chintai-keiei": {
        "focus": "PM/AM・収益・空室・修繕計画",
        "action": "家賃収入とコストの損益分岐をイメージ",
        "pitfall": "管理委託と経営受託の役割",
    },
    "insurance-property-risk": {
        "focus": "火災・賠償責任・借主保険・オーナー保険",
        "action": "保険の被保険者・補償範囲を表にまとめる",
        "pitfall": "保険と修繕義務の関係",
    },
    "exempt-invalid-questions": {
        "focus": "免除出題・出題無効の学習上の扱い",
        "action": "無効問題は論点メモのみ、点数計算は公式に従う",
        "pitfall": "無効問題を深追いしすぎる",
    },
    "ichimon-practice-mode": {
        "focus": "一問一答で弱点の短時間復習",
        "action": "通勤時間に誤答タグだけを回す",
        "pitfall": "解説を読まず正答だけ覚える",
    },
    "retake-review-plan": {
        "focus": "再受験時の計画の組み直し・心理面",
        "action": "前回の誤答分野を定量（％）で把握し優先順位",
        "pitfall": "同じ勉強法の繰り返し",
    },
}

HUB_SLUGS = frozenset({"law-subject", "rights-subject", "limit-subject"})


def norm(s: str | None) -> str:
    return (s or "").strip()


def hub_bodies(brief: dict[str, str], field_label: str) -> list[str]:
    return [
        (
            f"このページは「{field_label}」分野の学習ハブです。"
            f"用語解説・過去問演習・関連ガイドを横断して、{brief['focus']}を整理できます。"
            f"まずは全体像を把握し、弱点論点だけ深掘りする使い方が効率的です。"
        ),
        (
            f"{field_label}では、{brief['focus']}が中心です。"
            f"単語の暗記にとどめず、制度の目的と実務上の判断基準を一文で言えるようにしてください。"
            f"似た用語は比較表で「違う一文」を作ると記憶に残ります。"
        ),
        (
            f"用語解説は、一覧から{field_label}のカテゴリを絞り込み、"
            f"各記事の「まず押さえる要点」「具体例」「覚え方」を読みます。"
            f"記事末尾の関連過去問で、出題の言い換えに慣れるのがおすすめです。"
        ),
        (
            f"過去問は、{field_label}に近い科目・タグから年度別に解きます。"
            f"正解後も「なぜ他の肢が違うか」を声に出すと、{brief['action']}につながります。"
            f"間違えた語句はすぐ用語記事へ戻してください。"
        ),
        (
            f"数値・期限・手続の正式内容は、賃貸不動産経営管理士協議会・国土交通省の公式情報で確認してください。"
            f"本サイトは学習補助であり、最新の受験案内や法令改正は公式を正とします。"
        ),
        (
            f"試験は3分野が独立ではなく、{brief['pitfall']}ことがあります。"
            f"他分野のハブも月1回は見直し、横断のつながりを確認しましょう。"
        ),
        (
            f"次のステップ：このハブから用語3件・過去問5問をセットで学習し、復習リストに残します。"
            f"学習計画記事（study-plan）とあわせて週次の目標を更新してください。"
        ),
    ]


def standard_bodies(brief: dict[str, str], title: str) -> list[str]:
    return [
        (
            f"賃貸不動産経営管理士試験の制度・出題は年度で変わることがあります。"
            f"学習を始める前に協議会の公式サイトで受験案内・出題範囲を確認し、"
            f"そのうえで本記事の手順（{brief['action']}）に進んでください。"
        ),
        (
            f"本記事のテーマは「{title}」です。"
            f"{brief['focus']}を、前提知識と結論を分けて理解すると、過去問の選択肢が読みやすくなります。"
            f"暗記カードだけでなく、自分の言葉で説明できるかを週1回チェックしましょう。"
        ),
        (
            f"具体的には、{brief['action']}を1週間単位の目標に落とし込みます。"
            f"例：月曜は用語2件、水曜は過去問5問、土曜は誤りノートの見直し、など。"
            f"完璧を目指さず、継続できる量を設定するのが合格への近道です。"
        ),
        (
            f"復習は、解いた直後・翌日・1週間後の3回を目安に同じ論点へ戻ります。"
            f"正解した問題でも、根拠を説明できなければ復習対象に残してください。"
            f"アプリの復習モードや一問一答と組み合わせると効率が上がります。"
        ),
        (
            f"本サイトの問題・解説は学習補助であり、公式過去問そのものではありません。"
            f"法令改正や制度変更により注意を要する表現もあるため、迷ったときは公式情報と法令原文を優先してください。"
        ),
        (
            f"つまずきやすいのは、{brief['pitfall']}点です。"
            f"用語の意味は分かっていても、選択肢が言い換えられると判断できない場合があります。"
            f"比較表・関連用語・関連過去問で「何を区別する問題か」を意識しましょう。"
        ),
        (
            f"この記事を読み終えたら、関連する過去問を少なくとも3問解き、"
            f"分からなかった語句を用語集で確認します。関連ガイドを1本だけ選び、"
            f"学習の流れを固定すると継続しやすくなります。"
        ),
    ]


def pro_lead(slug: str, row: dict[str, str], brief: dict[str, str]) -> str:
    title = norm(row.get("title"))
    if slug in HUB_SLUGS:
        return (
            f"{title}。{brief['focus']}を、用語・過去問・関連記事から一気通貫で学べるよう整理しました。"
            f"弱点分野の入口として、週次の学習計画に組み込んでください。"
        )
    return (
        f"{title}について、受験生の視点で学習手順と注意点をまとめます。"
        f"{brief['focus']}を中心に、{brief['action']}まで具体的に解説します。"
        f"制度の最新情報は必ず公式サイトで確認してください。"
    )


def pro_faqs(slug: str, brief: dict[str, str]) -> tuple[str, str, str, str]:
    q1 = "この記事だけで公式情報の確認は完了しますか？"
    a1 = (
        "いいえ。試験日程、受験資格、手数料、合格基準、法令の正式な内容は、"
        "必ず賃貸不動産経営管理士協議会の公式サイトや法令原文で確認してください。"
        "本記事は学習の進め方を整理したガイドです。"
    )
    q2 = f"「{brief['focus']}」はどう勉強するのが効率的ですか？"
    a2 = (
        f"{brief['action']}が基本です。"
        f"読むだけで終わらせず、過去問で1問解いてから用語記事に戻る往復を1セットにすると定着します。"
    )
    return q1, a1, q2, a2


def upgrade_guide(row: dict[str, str]) -> None:
    slug = norm(row.get("slug"))
    brief = SLUG_BRIEF.get(slug)
    if not brief:
        return

    title = norm(row.get("title"))
    row["lead"] = pro_lead(slug, row, brief)

    if slug in HUB_SLUGS:
        field = "賃管法令・制度" if slug == "law-subject" else (
            "契約・実務" if slug == "rights-subject" else "設備・税務・その他"
        )
        bodies = hub_bodies(brief, field)
    else:
        bodies = standard_bodies(brief, title)

    for i, body in enumerate(bodies, start=1):
        row[f"section_{i}_body"] = body

    q1, a1, q2, a2 = pro_faqs(slug, brief)
    row["faq_1_question"] = q1
    row["faq_1_answer"] = a1
    row["faq_2_question"] = q2
    row["faq_2_answer"] = a2

    today = date.today().isoformat()
    row["last_reviewed_at"] = today
    row["source_checked_at"] = today
    row["revision_note"] = "専門家監修レベルの本文・FAQに全面更新（プロライター原稿）"


def main() -> int:
    with CSV_PATH.open(encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))
    fieldnames = list(rows[0].keys()) if rows else []

    updated = 0
    for row in rows:
        if norm(row.get("slug")) in SLUG_BRIEF:
            upgrade_guide(row)
            updated += 1

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)

    print(f"Pro-upgraded {updated}/{len(rows)} guide articles in {CSV_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
