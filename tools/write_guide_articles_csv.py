#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""data/guide_articles.csv を生成（試験ガイド・科目別ハブ）。"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "guide_articles.csv"

HEADER = [
    "slug",
    "genre",
    "title",
    "meta_description",
    "lead",
    "priority",
    "tags",
    "author_name",
    "author_profile",
    "reviewer_name",
    "reviewer_profile",
    "fact_checked_at",
    "primary_sources",
    "original_note",
    "user_intent",
    "action_items",
    "update_policy",
    "last_reviewed_at",
    "next_review_at",
    "source_checked_at",
    "content_status",
    "revision_note",
]
for i in range(1, 8):
    HEADER.extend([f"section_{i}_heading", f"section_{i}_body"])
for i in range(1, 3):
    HEADER.extend([f"faq_{i}_question", f"faq_{i}_answer"])
HEADER.append("related_links")

COMMON = {
    "author_name": "賃管マスター編集部",
    "author_profile": "賃貸不動産経営管理士試験の過去問形式演習、用語解説、学習導線を整理する編集チームです。",
    "reviewer_name": "賃管マスター確認担当",
    "reviewer_profile": "公開前に公式情報への誘導、断定表現、内部リンク、FAQ、更新日の有無を確認します。",
    "fact_checked_at": "2026-05-19",
    "primary_sources": "賃貸不動産経営管理士協議会（公式）|https://www.chintaikanrishi.jp/;国土交通省 住宅局|https://www.mlit.go.jp/jutakukentiku/house/",
    "update_policy": "試験要項や公式ページ、関係法令が更新されたタイミングで本文と参照元を見直します。",
    "last_reviewed_at": "2026-05-19",
    "next_review_at": "2026-08-19",
    "source_checked_at": "2026-05-19",
    "content_status": "published",
    "revision_note": "SEO記事テンプレート運用ルールに合わせ、目次・信頼性・FAQ・関連記事を整備。",
    "action_items": "公式情報を確認する;過去問形式の演習を解く;間違えた語句を用語集で確認する;復習対象に残す",
}

SECTIONS_STD = [
    ("最初に確認すること", "制度情報や日程、合格基準は年度で変わる可能性があります。学習前に賃貸不動産経営管理士協議会の公式サイトで最新の受験案内・出題範囲を確認し、そのうえで本サイトの演習・用語解説を使う流れにすると安心です。"),
    (
        "全体像・前提を分けて理解する",
        "賃貸不動産経営管理士試験は、賃管法令・制度、契約・実務、設備・税務などがつながって出題されます。単語の暗記だけでなく、制度の目的、実務上の判断、似た用語の違いを一文で説明できる状態を目標にしましょう。",
    ),
    (
        "具体的な進め方",
        "過去問形式の演習では、正答だけでなく「なぜ他の選択肢が違うか」まで確認します。読めなかった語句は用語解説記事へ戻り、関連語・法令根拠まで広げると定着しやすくなります。",
    ),
    (
        "復習・確認方法",
        "解いた直後・翌日・数日後と間隔を空けて同じ論点を解き直します。正解した問題でも根拠を説明できなければ復習対象に残してください。",
    ),
    (
        "注意点",
        "本サイトの問題・解説は学習補助であり、公式過去問そのものではありません。法令改正や制度変更により注意を要する表現もあるため、迷ったときは公式情報と法令原文を優先してください。",
    ),
    (
        "つまずきやすいポイント",
        "用語の意味は分かっていても、選択肢が言い換えられると判断できないケースが多いです。比較表や関連用語、関連過去問で「何を区別する問題か」を意識しましょう。",
    ),
    (
        "次にやること",
        "この記事を読んだら、関連する過去問を数問解き、分からなかった語句を用語集で確認します。科目別ハブや試験ガイドの関連記事を1本だけ選び、学習の流れを固定すると継続しやすくなります。",
    ),
]

FAQ_STD = [
    (
        "この記事だけで公式情報の確認は完了しますか？",
        "いいえ。試験日程、受験資格、手数料、合格基準、法令の正式な内容は、必ず協議会の公式サイトや法令原文で確認してください。",
    ),
    (
        "試験ガイドはどの順番で読むとよいですか？",
        "まず試験概要で全体像を確認し、科目別ハブで弱点分野を決め、過去問演習と用語解説を往復する流れがおすすめです。",
    ),
]


def article(
    slug: str,
    genre: str,
    title: str,
    meta: str,
    lead: str,
    priority: int,
    tags: str,
    user_intent: str,
    original_note: str,
    sections: list[tuple[str, str]] | None = None,
    related_links: str = "",
) -> dict[str, str]:
    row = dict(COMMON)
    row.update(
        {
            "slug": slug,
            "genre": genre,
            "title": title,
            "meta_description": meta,
            "lead": lead,
            "priority": str(priority),
            "tags": tags,
            "original_note": original_note,
            "user_intent": user_intent,
            "related_links": related_links,
        }
    )
    secs = sections or SECTIONS_STD
    for i, (h, b) in enumerate(secs[:7], start=1):
        row[f"section_{i}_heading"] = h
        row[f"section_{i}_body"] = b
    for i, (q, a) in enumerate(FAQ_STD, start=1):
        row[f"faq_{i}_question"] = q
        row[f"faq_{i}_answer"] = a.replace("この記事", f"「{title}」")
    return row


def hub_sections(field_label: str, term_hint: str, past_hint: str) -> list[tuple[str, str]]:
    return [
        (
            "このハブでできること",
            f"{field_label}分野の学習導線を1ページにまとめています。用語解説・過去問演習・関連ガイドへ進み、弱点論点を往復して定着させます。",
        ),
        (
            "押さえる論点の整理",
            f"{field_label}では、制度の目的、手続の流れ、実務上の判断基準がセットで問われます。{term_hint}を中心に、似た用語との違いを比較しながら覚えてください。",
        ),
        (
            "用語解説の使い方",
            f"用語解説一覧から{field_label}のカテゴリを絞り込み、各記事末尾の「関連過去問」で出題例を確認します。{term_hint}",
        ),
        (
            "過去問演習の進め方",
            f"過去問一覧またはアプリの演習モードで{field_label}に近い科目を選び、{past_hint}。間違えた語句は用語記事へ戻って関連語まで読みます。",
        ),
        (
            "法令・公式情報の確認",
            "数値・期限・手続の正式な内容は協議会・国交省の公式情報で確認してください。本サイトは学習補助であり、公式見解ではありません。",
        ),
        (
            "他分野とのつながり",
            "試験は3分野が独立ではなく、契約実務と法令、設備と税務がまたがって出ることがあります。苦手分野だけでなく、関連分野のハブもあわせて確認しましょう。",
        ),
        (
            "次のステップ",
            "このハブから用語1件・過去問3問をセットで学習し、復習リストに残します。余裕があれば他の試験ガイド記事も1本読み、学習計画を更新してください。",
        ),
    ]


ARTICLES = [
    article(
        "exam-overview",
        "試験概要",
        "賃貸不動産経営管理士試験とは？概要・出題分野・学習の進め方",
        "賃貸不動産経営管理士試験の概要、3分野の出題傾向、初学者向けの学習の進め方を整理します。",
        "試験概要を学習する受験生向けに、賃貸不動産経営管理士試験の位置づけと学習導線をまとめます。制度面は公式情報で確認しながら、過去問演習と用語解説で定着を図してください。",
        10,
        "試験概要",
        "試験の全体像と3分野の関係を把握したい。",
        "試験概要の学習導線と、過去問・用語集・科目別ハブへの内部リンクを整理した記事です。",
        related_links="study-plan:独学・初学者向けの学習計画の立て方;past-questions-how-to-use:過去問の効果的な使い方",
    ),
    article(
        "study-plan",
        "試験対策",
        "賃貸不動産経営管理士の独学・初学者向け学習計画の立て方",
        "仕事や家事と両立しながら、賃管試験の学習計画を立てる手順と週次の進め方を整理します。",
        "初学者・独学の受験生向けに、公式確認→分野別ハブ→過去問→用語の循環で計画を立てる方法を説明します。",
        20,
        "学習計画;独学",
        "限られた時間で効率よく学習を進めたい。",
        "学習計画テンプレートと科目別ハブへの導線を整備した記事です。",
        related_links="exam-overview:賃貸不動産経営管理士試験とは？概要・出題分野・学習の進め方;law-subject:賃管法令・制度の学習ハブ",
    ),
    article(
        "past-questions-how-to-use",
        "過去問活用",
        "賃管試験の過去問の効果的な使い方（演習モード・復習の回し方）",
        "過去問形式の演習を何周するか、間違えた問題の記録の仕方、用語解説との往復を整理します。",
        "過去問をただ解く回数を増やすのではなく、弱点論点を用語・ガイド記事へつなげる使い方をまとめます。",
        30,
        "過去問;復習",
        "過去問演習を効率よく復習に活かしたい。",
        "過去問一覧・用語記事の関連過去問ブロックへの導線を強化する記事です。",
        related_links="exam-overview:賃貸不動産経営管理士試験とは？概要・出題分野・学習の進め方;rights-subject:契約・実務の学習ハブ",
    ),
    article(
        "law-subject",
        "科目別対策",
        "【科目別ハブ】賃管法令・制度の学習導線（用語・過去問・関連記事）",
        "賃貸住宅管理業法を中心とした賃管法令・制度分野の学習ハブ。用語解説・過去問・関連ガイドへの入口をまとめます。",
        "賃管法令・制度分野の弱点を、用語→過去問→公式確認の順で整理したい受験生向けのハブページです。",
        40,
        "科目別;賃管法令;ハブ",
        "法令・制度分野を体系的に学び直したい。",
        "科目別ハブ（law）として用語索引・過去問・試験ガイドを横断リンクする設計の記事です。",
        sections=hub_sections(
            "賃管法令・制度",
            "登録制度、業務範囲、重要事項説明、維持保全などの用語",
            "賃貸住宅管理業法・関連法令のカテゴリから年度別に解く",
        ),
        related_links="exam-overview:賃貸不動産経営管理士試験とは？概要・出題分野・学習の進め方;rights-subject:【科目別ハブ】契約・実務の学習導線;limit-subject:【科目別ハブ】設備・税務・その他の学習導線",
    ),
    article(
        "rights-subject",
        "科目別対策",
        "【科目別ハブ】契約・実務の学習導線（用語・過去問・関連記事）",
        "借地借家法・賃貸借契約・原状回復・管理実務など、契約・実務分野の学習ハブです。",
        "契約・実務分野で迷いやすい論点を、用語解説と過去問で往復しながら整理するための入口ページです。",
        50,
        "科目別;契約実務;ハブ",
        "契約・実務分野の得点源を固めたい。",
        "科目別ハブ（rights）として用語・過去問を束ねる設計の記事です。",
        sections=hub_sections(
            "契約・実務",
            "定期借家、敷金、原状回復、管理受託などの用語",
            "賃貸借契約・原状回復・管理実務の問題を中心に演習する",
        ),
        related_links="law-subject:【科目別ハブ】賃管法令・制度の学習導線;limit-subject:【科目別ハブ】設備・税務・その他の学習導線;past-questions-how-to-use:賃管試験の過去問の効果的な使い方",
    ),
    article(
        "limit-subject",
        "科目別対策",
        "【科目別ハブ】設備・税務・その他の学習導線（用語・過去問・関連記事）",
        "建物・設備、会計・税務・保険、賃貸経営・PM/AMなど、設備・税務・その他分野の学習ハブです。",
        "設備・税務分野は用語と数値・手続が混在しやすいため、用語記事と過去問をセットで確認する導線を示します。",
        60,
        "科目別;設備税務;ハブ",
        "設備・税務分野の暗記と理解のバランスを取りたい。",
        "科目別ハブ（limit）として用語・過去問を束ねる設計の記事です。",
        sections=hub_sections(
            "設備・税務・その他",
            "建物設備、減価償却、保険、PM/AMなどの用語",
            "建物・設備・会計税務のカテゴリから演習する",
        ),
        related_links="law-subject:【科目別ハブ】賃管法令・制度の学習導線;rights-subject:【科目別ハブ】契約・実務の学習導線",
    ),
    article(
        "chintai-gyoho-basics",
        "法令対策",
        "賃貸住宅管理業法の試験対策｜登録・業務・監督の押さえ方",
        "賃貸住宅管理業法の主要テーマ（登録、業務、監督、重要事項説明など）を試験向けに整理します。",
        "法令分野の中でも出題の多い賃貸住宅管理業法に絞り、用語と過去問で確認する手順をまとめます。",
        70,
        "賃貸住宅管理業法;法令",
        "賃貸住宅管理業法の論点を体系的に復習したい。",
        "法令対策記事。law-subject ハブからの深掘り用。",
        related_links="law-subject:【科目別ハブ】賃管法令・制度の学習導線;exam-overview:賃貸不動産経営管理士試験とは？概要・出題分野・学習の進め方",
    ),
    article(
        "genjo-kaifuku-guide",
        "重要論点",
        "原状回復の試験対策｜特約・ガイドライン・費用負担の整理",
        "原状回復をめぐる特約、ガイドライン、費用負担の考え方を試験向けに整理します。",
        "契約・実務で頻出の原状回復について、用語解説と過去問で確認する論点をまとめます。",
        80,
        "原状回復;契約実務",
        "原状回復の特約とガイドラインの違いを整理したい。",
        "rights-subject ハブからの深掘り用の重要論点記事です。",
        related_links="rights-subject:【科目別ハブ】契約・実務の学習導線;past-questions-how-to-use:賃管試験の過去問の効果的な使い方",
    ),
]


def main() -> int:
    rows: list[dict[str, str]] = []
    for src in ARTICLES:
        row = dict.fromkeys(HEADER, "")
        row.update({k: src.get(k, "") for k in HEADER})
        rows.append(row)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=HEADER, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)
    print(f"Wrote {len(rows)} rows to {OUT}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
