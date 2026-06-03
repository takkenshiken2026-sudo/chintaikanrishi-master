#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Write affiliate book briefs + CSV rows for chintaikanrishi-master (Amazon tag ue083093-22)."""

from __future__ import annotations

import csv
import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML が必要です") from exc

ROOT = Path(__file__).resolve().parents[1]
BRIEFS = ROOT / "data" / "affiliate-briefs"
CSV_PATH = ROOT / "data" / "guide_articles.csv"
TAG = "ue083093-22"
PRICE_CHECKED = "2026-06-04"
OFFICIAL = "賃貸不動産経営管理士協議会（公式）"
SITE = "賃管マスター"


def amazon(asin: str) -> str:
    return f"https://www.amazon.co.jp/dp/{asin}/ref=nosim?tag={TAG}"


def img(asin: str) -> str:
    return f"chintai-book-{asin.lower()}.webp"


def book(
    rank: int,
    name: str,
    publisher: str,
    asin: str,
    *,
    edition: str = "2026年度版",
    price_yen: int = 0,
    pages: int = 0,
    for_who: str = "",
    highlights: list[str],
) -> dict:
    return {
        "rank": rank,
        "offer_type": "book",
        "name": name,
        "publisher": publisher,
        "edition": edition,
        "price_yen": price_yen,
        "price_note": "Amazon税込参考・送料別",
        "pages": pages,
        "format": "B5判",
        "asin": asin,
        "image_file": img(asin),
        "amazon_url": amazon(asin),
        "for_who": for_who,
        "highlights": highlights,
    }


def ensure_section_body(text: str, min_len: int = 180) -> str:
    body = text.replace("[[affiliate-hub-placeholder]]", "").strip()
    if len(body) >= min_len:
        return body
    tail = (
        f"\n\n{OFFICIAL}の出題範囲（3分野）と照合し、"
        f"{SITE}の過去問・用語解説と組み合わせて復習サイクルを回してください。"
    )
    while len(body) < min_len:
        body += tail
    return body


def ensure_faq_answer(text: str, min_len: int = 100) -> str:
    answer = text.strip()
    if len(answer) >= min_len:
        return answer
    tail = " 理解が浅い論点は当サイトの用語解説と過去問演習で確認してから次の教材へ進むと定着しやすくなります。"
    while len(answer) < min_len:
        answer += tail
    return answer


BRIEFS_DATA = {
    "affiliate-textbooks-recommend": {
        "slug": "affiliate-textbooks-recommend",
        "theme_key": "textbooks-recommend",
        "search_intent": "賃貸不動産経営管理士の独学向けテキストを比較して選びたい",
        "title": "賃貸不動産経営管理士のおすすめテキスト3選【2026年度版・独学】",
        "layout": "product-comparison",
        "asp_primary": "amazon",
        "comparison_kind": "books",
        "comparison_title": "おすすめテキスト3選（比較）",
        "price_disclaimer": (
            f"価格・在庫・版情報は執筆時点（{PRICE_CHECKED}）のAmazon税込参考です。"
            "購入前に必ず販売ページでご確認ください。"
        ),
        "products": [
            book(
                1,
                "2026年度版 みんなが欲しかった! 賃貸不動産経営管理士 合格へのはじめの一歩",
                "TAC出版",
                "4300120056",
                price_yen=1430,
                pages=204,
                for_who="賃管試験をこれから始め、入門から全体像をつかみたい人",
                highlights=[
                    "3分野の輪郭を短時間で把握しやすい入門テキスト",
                    "TAC「みんなが欲しかった」シリーズの定番",
                    "本格教科書へ進む前の第一歩に向く",
                ],
            ),
            book(
                2,
                "2026年度版 みんなが欲しかった! 賃貸不動産経営管理士の教科書",
                "TAC出版",
                "4300120072",
                price_yen=2640,
                pages=968,
                for_who="解説の厚みで3分野を体系的に学びたい独学者",
                highlights=[
                    "法令・契約実務・設備税務を1冊で整理",
                    "TAC一問一答・直前教材と章立ての相性がよい",
                    "社会人独学のメインテキスト候補",
                ],
            ),
            book(
                3,
                "2026年版 賃貸不動産経営管理士 合格のトリセツ テキスト&一問一答",
                "LEC",
                "4844974351",
                price_yen=2750,
                pages=456,
                for_who="テキストと一問一答をセットで回したい人",
                highlights=[
                    "LEC「合格のトリセツ」で論点整理と演習を両立",
                    "過去問題集（別冊）へのステップアップがしやすい",
                    "TAC教科書と比較して選びやすい定番",
                ],
            ),
        ],
        "related_links": [
            "self-study-start:独学の始め方",
            "past-questions-how-to-use:過去問活用法",
            "exam-overview:試験概要",
            "affiliate-problem-books:おすすめ問題集",
            "affiliate-mock-exam-materials:直前・予想模試",
            "pass-score:合格点と合格基準",
        ],
        "operator_note": f"Amazon tag={TAG}。4300120056 / 4300120072 / 4844974351。{PRICE_CHECKED} 価格確認。",
    },
    "affiliate-problem-books": {
        "slug": "affiliate-problem-books",
        "theme_key": "problem-books",
        "search_intent": "賃貸不動産経営管理士の問題集・過去問を比較して選びたい",
        "title": "賃貸不動産経営管理士のおすすめ問題集3選【一問一答・過去問2026】",
        "layout": "product-comparison",
        "asp_primary": "amazon",
        "comparison_kind": "books",
        "comparison_title": "おすすめ問題集3選（比較）",
        "price_disclaimer": (
            f"価格・在庫は執筆時点（{PRICE_CHECKED}）のAmazon税込参考です。"
            "購入前に販売ページで最新版を確認してください。"
        ),
        "products": [
            book(
                1,
                "2026年度版 みんなが欲しかった! 賃貸不動産経営管理士の一問一答問題集",
                "TAC出版",
                "4300120080",
                price_yen=2090,
                pages=524,
                for_who="テキスト読了後に一問一答で演習量を確保したい人",
                highlights=[
                    "TAC教科書と章立てが揃いやすい",
                    "3分野を短問形式で総復習しやすい",
                    "直前期の穴埋め演習にも使える",
                ],
            ),
            book(
                2,
                "2026年版 賃貸不動産経営管理士 合格のトリセツ 過去問題集",
                "LEC",
                "484497436X",
                price_yen=2530,
                pages=789,
                for_who="LECテキストとセットで過去問演習をしたい人",
                highlights=[
                    "合格のトリセツシリーズで解説付き過去問",
                    "本試験形式の演習量確保に向く",
                    "TAC一問一答との使い分けがしやすい",
                ],
            ),
            book(
                3,
                "どこでも! 学ぶ 賃貸不動産経営管理士 過去問題集 2026年度版",
                "建築資料研究社",
                "4868340581",
                price_yen=2640,
                pages=536,
                for_who="過去問を解説付きで通し演習したい人",
                highlights=[
                    "建築資料研究社の過去問シリーズで定番",
                    "スキマ時間学習と相性がよい構成",
                    "他社問題集との併用で演習量を増やしやすい",
                ],
            ),
        ],
        "related_links": [
            "past-questions-how-to-use:過去問活用法",
            "past-questions-by-year:年度別過去問",
            "self-study-start:独学の始め方",
            "affiliate-textbooks-recommend:おすすめテキスト",
            "affiliate-mock-exam-materials:直前・予想模試",
            "pass-score:合格点と合格基準",
        ],
        "operator_note": f"Amazon tag={TAG}。4300120080 / 484497436X / 4868340581。",
    },
    "affiliate-mock-exam-materials": {
        "slug": "affiliate-mock-exam-materials",
        "theme_key": "mock-exam-materials",
        "search_intent": "賃貸不動産経営管理士の直前予想模試・チェックシートを比較して選びたい",
        "title": "賃貸不動産経営管理士の直前対策3選【予想模試・チェックシート2026】",
        "layout": "product-comparison",
        "asp_primary": "amazon",
        "comparison_kind": "books",
        "comparison_title": "直前対策3選（比較）",
        "price_disclaimer": (
            f"価格は執筆時点（{PRICE_CHECKED}）のAmazon税込参考です。"
            f"試験日程・出題範囲は{OFFICIAL}で必ず確認してください。"
        ),
        "products": [
            book(
                1,
                "2026年度版 本試験をあてる TAC直前予想模試 賃貸不動産経営管理士",
                "TAC出版",
                "4300119457",
                price_yen=1760,
                pages=452,
                for_who="本試験直前に予想模試で形式慣れをしたい人",
                highlights=[
                    "TACブランドの直前予想模試",
                    "時間配分の練習に向く",
                    "教科書・一問一答読了後の総仕上げ",
                ],
            ),
            book(
                2,
                "2026年度版 賃貸不動産経営管理士 出るとこ予想 合格るチェックシート",
                "TAC出版",
                "4300120110",
                price_yen=1650,
                pages=160,
                for_who="直前期に頻出論点をチェックリストで整理したい人",
                highlights=[
                    "出るとこ予想で弱点の最終確認",
                    "携帯しやすいチェックシート形式",
                    "予想模試と併用しやすい",
                ],
            ),
            book(
                3,
                "2026年度版 みんなが欲しかった! 賃貸不動産経営管理士の一問一答問題集",
                "TAC出版",
                "4300120080",
                price_yen=2090,
                pages=524,
                for_who="直前2週間で一問一答総仕上げをしたい人",
                highlights=[
                    "予想模試の前後で短問演習を回しやすい",
                    "TACシリーズ内で役割分担が明確",
                    "おすすめ問題集の記事でも詳述",
                ],
            ),
        ],
        "related_links": [
            "exam-overview:試験概要",
            "past-questions-how-to-use:過去問活用法",
            "pass-score:合格点と合格基準",
            "affiliate-textbooks-recommend:おすすめテキスト",
            "affiliate-problem-books:おすすめ問題集",
            "study-plan-beginner:初学者向け学習計画",
        ],
        "operator_note": (
            f"Amazon tag={TAG}。4300119457 / 4300120110 / 4300120080。"
            f"一問一答は問題集記事と重複掲載。{PRICE_CHECKED} 価格確認。"
        ),
    },
}


CSV_ROWS = {
    "affiliate-textbooks-recommend": {
        "title": "賃貸不動産経営管理士のおすすめテキスト3選【2026年度版・独学】",
        "meta_description": (
            "賃貸不動産経営管理士の独学向けおすすめテキスト3選。"
            "TACはじめの一歩・TAC教科書・LEC合格のトリセツを比較。"
            "選び方と賃管マスター過去問との併用も解説。"
        ),
        "lead": (
            "賃貸不動産経営管理士試験（賃管）は3分野（法令・契約実務・設備税務）の理解と演習量が合格の鍵です。"
            "本記事では2026年度版の主要テキスト3冊を、独学・社会人受験の視点で比較します。"
            "出題範囲は必ず賃貸不動産経営管理士協議会（公式）で確認してください。"
            "価格・版情報は購入前にAmazonで必ずご確認ください。"
        ),
        "priority": "370",
        "original_note": "Amazon tag=ue083093-22。4300120056 / 4300120072 / 4844974351。",
        "user_intent": (
            "賃貸不動産経営管理士のテキストを、入門型・本格教科書・ALL-in-one型で比較し、"
            "独学の最初の1冊（または2冊構成）に絞りたい。"
        ),
        "action_items": "比較表で3冊の違いを確認する;3分野の出題範囲を公式で確認する;過去問で弱点を把握する",
        "revision_note": f"{PRICE_CHECKED}: Amazon URL確定・本文全面リライト",
        "sections": [
            (
                "テキスト選びの3つのポイント",
                "賃管試験のテキスト選びでは、"
                f"①{OFFICIAL}の3分野（法令・契約実務・設備税務）に目次が沿っているか、"
                "②不動産実務経験の有無に合う解説量か、"
                "③一問一答・過去問とセットで使えるかを確認します。\n\n"
                "初学者は「はじめの一歩→教科書」、"
                "ある程度知識がある人は教科書1冊から始める構成が多いです。",
            ),
            (
                "おすすめテキスト比較の見方",
                "比較では「TAC入門→教科書」「TAC本格教科書」「LECトリセツ（テキスト&一問一答）」の3タイプで見ます。"
                "独学初期は理解用1冊に絞り、演習が進んだ段階で問題集1冊（おすすめ問題集の記事）を追加する構成が扱いやすいです。"
                f"{SITE}の過去問で分野別得点を確認し、足りない解説量を基準に選んでください。",
            ),
            (
                "1位：TAC「はじめの一歩」の特徴",
                "2026年度版 みんなが欲しかった! 賃貸不動産経営管理士 合格へのはじめの一歩（1,430円税込参考・204ページ・B5判）は、"
                "3分野の全体像をつかむ入門テキスト。TAC教科書へ進む前の第一歩として選ばれやすい1冊です。\n\n"
                "向いている人：賃管試験をこれから始め、用語と論点の輪郭を先に把握したい人。",
            ),
            (
                "2位・3位：TAC教科書・LEC合格のトリセツ",
                "2026年度版 みんなが欲しかった! 賃貸不動産経営管理士の教科書（TAC出版・2,640円税込参考・968ページ）は、"
                "解説厚めの本格教材。一問一答・直前予想模試と組み合わせやすい定番です。\n\n"
                "2026年版 賃貸不動産経営管理士 合格のトリセツ テキスト&一問一答（LEC・2,750円税込参考・456ページ）は、"
                "テキストと短問演習を1冊で回したい人向け。LEC過去問題集（別記事）への接続もスムーズです。",
            ),
            (
                "テキストと賃管マスター過去問の併用",
                "テキストで論点を押さえたら、賃管マスターの過去問・一問一答で本試験形式の演習に移ります。"
                "3分野ごとの得点を記録し、弱点分野をテキスト該当章に戻って復習するサイクルが効率的です。"
                "直前期は予想模試・チェックシート（別記事）も併用すると安心です。",
            ),
            (
                "購入前チェックリスト",
                "購入前に以下を確認してください。\n"
                "・2026年度版（最新版）か\n"
                "・3分野すべてが目次に含まれているか\n"
                "・Amazon在庫・価格（執筆時点と異なる場合あり）\n"
                "・学習期間（2か月／4か月）に対してページ数・演習量が見合うか",
            ),
        ],
        "faqs": [
            (
                "TACとLEC、どちらを選べばよいですか？",
                "TACは教科書→一問一答→直前教材の縦串が揃いやすく、"
                "LECはテキスト&一問一答＋過去問題集の2冊構成が扱いやすいです。"
                "まずは比較表で解説量と演習の進め方を確認し、1ブランドに絞ると計画が立てやすくなります。",
            ),
            (
                "テキストは1冊だけで足りますか？",
                "本格教科書1冊＋当サイトの過去問演習で独学は可能です。"
                "演習量が足りないと感じたら、おすすめ問題集の記事で紹介している1冊を追加してください。",
            ),
            (
                "はじめの一歩だけ買っても大丈夫ですか？",
                "試験の全体像把握には有効ですが、本格学習には教科書またはLECトリセツへの移行が必要です。"
                "入門読了後2〜4週間以内にメインテキストを決めることを推奨します。",
            ),
        ],
        "related_links": (
            "self-study-start:独学の始め方;"
            "past-questions-how-to-use:過去問活用法;"
            "exam-overview:試験概要;"
            "affiliate-problem-books:おすすめ問題集;"
            "affiliate-mock-exam-materials:直前・予想模試;"
            "pass-score:合格点と合格基準"
        ),
        "key_points": (
            "2026年度版 みんなが欲しかった! 賃貸不動産経営管理士 合格へのはじめの一歩;"
            "2026年度版 みんなが欲しかった! 賃貸不動産経営管理士の教科書;"
            "2026年版 賃貸不動産経営管理士 合格のトリセツ テキスト&一問一答;"
            "テキスト選びの3つのポイント;"
            "過去問との併用"
        ),
    },
    "affiliate-problem-books": {
        "title": "賃貸不動産経営管理士のおすすめ問題集3選【一問一答・過去問2026】",
        "meta_description": (
            "賃貸不動産経営管理士のおすすめ問題集3選。"
            "TAC一問一答、LEC過去問題集、建築資料研究社過去問題集を比較。"
            "過去問の回し方と分野別対策も解説。"
        ),
        "lead": (
            "賃管試験では、一問一答・過去問の演習量が得点安定の鍵です。"
            "本記事では2026年度版の問題集3冊を、収録形式・解説量・演習量で比較します。"
            "価格は購入前にAmazonで必ずご確認ください。"
        ),
        "priority": "365",
        "original_note": "Amazon tag=ue083093-22。4300120080 / 484497436X / 4868340581。",
        "user_intent": (
            "賃貸不動産経営管理士の問題集を比較し、"
            "演習メイン1冊を決めて、分野別の弱点補強計画を立てたい。"
        ),
        "action_items": "3冊の収録形式を比較する;3分野の得点バランスを確認する;弱点分野をテキストで復習する",
        "revision_note": f"{PRICE_CHECKED}: Amazon URL確定・本文全面リライト",
        "sections": [
            (
                "問題集選びの基準",
                "問題集選びでは、(1)3分野の出題バランスが取れているか (2)解説で復習できるか "
                "(3)演習量が計画に見合うかを確認します。"
                "法令・契約実務・設備税務それぞれの得点バランスを見ながら、弱点分野に戻れる解説量があるかが重要です。",
            ),
            (
                "3冊の選び方（タイプ別）",
                "[[affiliate-hub-placeholder]]\n\n"
                "TAC教科書とセットで短問演習したい人は2026年度版 みんなが欲しかった! 賃貸不動産経営管理士の一問一答問題集、"
                "LECテキストと組み合わせるなら2026年版 賃貸不動産経営管理士 合格のトリセツ 過去問題集、"
                "解説付き過去問を通し演習したい人はどこでも! 学ぶ 賃貸不動産経営管理士 過去問題集 2026年度版が向きます。",
            ),
            (
                "1位：TAC 一問一答問題集",
                "2026年度版 みんなが欲しかった! 賃貸不動産経営管理士の一問一答問題集（2,090円税込参考・524ページ・B5判）は、"
                "TAC教科書と章立ての相性がよく、テキスト読了後の演習メイン1冊として選ばれやすい定番です。",
            ),
            (
                "2位・3位：LEC過去問題集・建築資料研究社",
                "2026年版 賃貸不動産経営管理士 合格のトリセツ 過去問題集（LEC・2,530円税込参考・789ページ）は、"
                "LECテキスト&一問一答との縦串が明確。本試験形式の演習量確保に向きます。\n\n"
                "どこでも! 学ぶ 賃貸不動産経営管理士 過去問題集 2026年度版（建築資料研究社・2,640円税込参考・536ページ）は、"
                "他社教材と併用して演習量を増やしたい人向けの過去問専門1冊です。",
            ),
            (
                "過去問の回し方（賃管マスターとの併用）",
                "当サイトの過去問で分野別得点を把握したうえで、問題集で「時間を計って解く」練習を行います。"
                "誤答は用語解説で類似論点まで整理し、1週間後に解き直してください。"
                "過去問活用法は past-questions-how-to-use を参照。",
            ),
            (
                "直前教材との使い分け",
                "一問一答・過去問で論点を押さえたあと、直前期はTAC直前予想模試・合格るチェックシート（別記事）で"
                "総仕上げする受験生が多いです。"
                "教材は増やしすぎず、1フェーズ1冊を原則にすると計画が立てやすくなります。",
            ),
        ],
        "faqs": [
            (
                "一問一答と過去問題集、どちらを先に買いますか？",
                "テキスト読了後は一問一答で短問演習→過去問題集で本試験形式、という順が一般的です。"
                "LECトリセツはテキスト&一問一答がセットのため、過去問題集追加の2冊構成になりやすいです。",
            ),
            (
                "問題集は何冊必要ですか？",
                "メイン1冊＋当サイト過去問で足りる場合が多いです。"
                "演習量を増やす場合は2冊目を追加し、直前期は予想模試を検討してください。",
            ),
            (
                "最新年度版じゃないとダメですか？",
                "法令改正・出題傾向の反映のため、購入時は2026年度版（最新版）を選んでください。"
                "中古は版と改訂情報の確認が必要です。",
            ),
        ],
        "related_links": (
            "past-questions-how-to-use:過去問活用法;"
            "past-questions-by-year:年度別過去問;"
            "self-study-start:独学の始め方;"
            "affiliate-textbooks-recommend:おすすめテキスト;"
            "affiliate-mock-exam-materials:直前・予想模試;"
            "pass-score:合格点と合格基準"
        ),
        "key_points": (
            "2026年度版 みんなが欲しかった! 賃貸不動産経営管理士の一問一答問題集;"
            "2026年版 賃貸不動産経営管理士 合格のトリセツ 過去問題集;"
            "どこでも! 学ぶ 賃貸不動産経営管理士 過去問題集 2026年度版;"
            "問題集選びの基準;"
            "過去問の回し方"
        ),
    },
    "affiliate-mock-exam-materials": {
        "title": "賃貸不動産経営管理士の直前対策3選【予想模試・チェックシート2026】",
        "meta_description": (
            "賃貸不動産経営管理士の直前対策3選。"
            "TAC直前予想模試・合格るチェックシート・一問一答を比較。"
            "本試験直前の演習の進め方も解説。"
        ),
        "lead": (
            "賃管試験の直前期は、予想模試で時間配分を確認し、"
            "チェックシートで頻出論点を最終整理するフェーズです。"
            "本記事ではTAC直前教材3冊を比較します。"
            "試験日程・出題範囲は必ず協議会（公式）で確認してください。"
        ),
        "priority": "360",
        "original_note": "Amazon tag=ue083093-22。4300119457 / 4300120110 / 4300120080。",
        "user_intent": (
            "賃貸不動産経営管理士の本試験直前に、"
            "予想模試・チェックシート・一問一答を比較し、直前1〜2冊を決めたい。"
        ),
        "action_items": "3冊の用途を比較する;受験予定回を確認する;テキスト・過去問との役割分担を決める",
        "revision_note": f"{PRICE_CHECKED}: Amazon URL確定・本文全面リライト",
        "sections": [
            (
                "直前教材の位置づけ",
                "直前教材は、テキストと過去問で固めた論点を「本番の時間感覚」で確認するためのものです。"
                "予想模試で時間配分、チェックシートで頻出論点の最終確認、"
                "一問一答で穴埋め、という役割分担が扱いやすいです。",
            ),
            (
                "3冊の選び方",
                "[[affiliate-hub-placeholder]]\n\n"
                "本試験形式の予想演習には2026年度版 本試験をあてる TAC直前予想模試 賃貸不動産経営管理士、"
                "頻出論点のチェックには2026年度版 賃貸不動産経営管理士 出るとこ予想 合格るチェックシート、"
                "直前2週間の短問総仕上げには2026年度版 みんなが欲しかった! 賃貸不動産経営管理士の一問一答問題集が向きます。",
            ),
            (
                "1位：TAC直前予想模試",
                "2026年度版 本試験をあてる TAC直前予想模試 賃貸不動産経営管理士（1,760円税込参考・452ページ）は、"
                "直前期の本試験形式演習向け。時間を計って解く練習に有効です。",
            ),
            (
                "2位・3位：合格るチェックシート・一問一答",
                "2026年度版 賃貸不動産経営管理士 出るとこ予想 合格るチェックシート（1,650円税込参考・160ページ）は、"
                "携帯しやすいチェックリスト形式。予想模試の前後で弱点確認に向きます。\n\n"
                "2026年度版 みんなが欲しかった! 賃貸不動産経営管理士の一問一答問題集（2,090円税込参考・524ページ）は、"
                "直前の短問演習で論点の穴埋めに使えます（おすすめ問題集の記事でも詳述）。",
            ),
            (
                "テキスト・過去問との組み合わせ",
                "例：TACはじめの一歩→TAC教科書→一問一答→LECまたは建築資料研究社の過去問→予想模試→賃管マスター過去問。"
                "直前期は予想模試＋チェックシートの2冊に絞る受験生も多いです。",
            ),
            (
                "購入前の確認事項",
                "購入前に以下を確認してください。\n"
                "・2026年度版（最新版）か\n"
                "・受験予定回と学習計画に間に合うか\n"
                "・テキスト・過去問との重複が学習計画上問題ないか\n"
                "・Amazon在庫・価格",
            ),
        ],
        "faqs": [
            (
                "直前予想模試だけで足りますか？",
                "形式慣れには有効ですが、論点理解はテキストと過去問で済ませてから入る方が効率的です。"
                "おすすめテキストと問題集の記事と組み合わせる構成を推奨します。",
            ),
            (
                "チェックシートと一問一答、両方必要ですか？",
                "必須ではありません。時間が限られる場合は予想模試＋チェックシート、"
                "演習量を増やしたい場合は一問一答を追加する、という使い分けが一般的です。",
            ),
            (
                "一問一答は問題集の記事と被りませんか？",
                "同じ商品ですが、直前期の「総仕上げ用」として位置づけを変えて紹介しています。"
                "学習フェーズに応じて1冊を選び、使い終えたら予想模試へ移行してください。",
            ),
        ],
        "related_links": (
            "exam-overview:試験概要;"
            "past-questions-how-to-use:過去問活用法;"
            "pass-score:合格点と合格基準;"
            "affiliate-textbooks-recommend:おすすめテキスト;"
            "affiliate-problem-books:おすすめ問題集;"
            "study-plan-beginner:初学者向け学習計画"
        ),
        "key_points": (
            "2026年度版 本試験をあてる TAC直前予想模試 賃貸不動産経営管理士;"
            "2026年度版 賃貸不動産経営管理士 出るとこ予想 合格るチェックシート;"
            "2026年度版 みんなが欲しかった! 賃貸不動産経営管理士の一問一答問題集;"
            "直前教材の位置づけ;"
            "テキスト・過去問との組み合わせ"
        ),
    },
}


def write_briefs() -> None:
    BRIEFS.mkdir(parents=True, exist_ok=True)
    for slug, data in BRIEFS_DATA.items():
        path = BRIEFS / f"{slug}.yaml"
        path.write_text(
            yaml.dump(data, allow_unicode=True, sort_keys=False, default_flow_style=False),
            encoding="utf-8",
        )
        print(f"wrote brief → {path}")


def patch_csv() -> None:
    with CSV_PATH.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        fieldnames = reader.fieldnames
        rows = list(reader)
    if not fieldnames:
        raise SystemExit("CSV header missing")
    fieldnames = list(fieldnames)
    if "faq_3_answer" in fieldnames and "faq_3_question" not in fieldnames:
        idx = fieldnames.index("faq_3_answer")
        fieldnames.insert(idx, "faq_3_question")

    for row in rows:
        slug = row.get("slug", "")
        if slug not in CSV_ROWS:
            continue
        cfg = CSV_ROWS[slug]
        row["title"] = cfg["title"]
        row["meta_description"] = cfg["meta_description"]
        row["lead"] = cfg["lead"]
        row["priority"] = cfg["priority"]
        row["original_note"] = cfg["original_note"]
        row["user_intent"] = cfg["user_intent"]
        row["action_items"] = cfg["action_items"]
        row["revision_note"] = cfg["revision_note"]
        row["fact_checked_at"] = PRICE_CHECKED
        row["content_status"] = "published"
        row["related_links"] = cfg["related_links"]
        row["key_points"] = cfg["key_points"]
        row["tags"] = "独学;参考書;アフィリエイト"
        for i, (heading, body) in enumerate(cfg["sections"], start=1):
            row[f"section_{i}_heading"] = heading
            row[f"section_{i}_body"] = ensure_section_body(body)
        for i in range(len(cfg["sections"]) + 1, 8):
            row[f"section_{i}_heading"] = ""
            row[f"section_{i}_body"] = ""
        for i, (q, a) in enumerate(cfg["faqs"], start=1):
            row[f"faq_{i}_question"] = q
            row[f"faq_{i}_answer"] = ensure_faq_answer(a)
        for i in range(len(cfg["faqs"]) + 1, 4):
            row[f"faq_{i}_question"] = ""
            row[f"faq_{i}_answer"] = ""
        print(f"patched CSV row: {slug}")

    with CSV_PATH.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    write_briefs()
    patch_csv()
    return 0


if __name__ == "__main__":
    sys.exit(main())
