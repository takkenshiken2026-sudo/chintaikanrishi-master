#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Phase5: archived高表示URLの統合先記事強化（FAQ追記）。"""

from __future__ import annotations

REWRITES: dict[str, dict[str, str]] = {
    "exam-overview": {
        "faq_4_question": "初学者でも賃管試験は受けられますか？難易度は？",
        "faq_4_answer": (
            "受験資格を満たせば初学者でも受験できます。難易度は統計だけでなく演習データで見るのが確実です。"
            "例えば6/14（日）要項5項目メモ→6/21（日）3分野演習10問で正答7問以上→7/5（日）50問120分通しを目安に、"
            "35/50未満の分野に翌週+2時間振り替えると初学者向けの進め方が再現できます。"
            "詳細は試験難易度記事と併読してください（旧「初学者向け難易度」記事の要点を統合）。"
        ),
        "revision_note": "2026-06-18: GSC Phase5（archived difficulty-for-beginners 統合）",
    },
    "study-plan": {
        "faq_4_question": "過去問は年度別に何年分使えばよいですか？",
        "faq_4_answer": (
            "要項の出題範囲に合う年度から逆算し、直近3〜5年を週次枠に組み込むのが定番です。"
            "例えば6/28（日）に直近3年×分野別15問を解き、誤答3語を記録→7/5（日）に解き直し12問以上、"
            "最新年度は11/1（日）の50問通し前に弱点分野へ再配置します（旧「年度別過去問」「最新年度」記事の要点を統合）。"
            "使い方の手順は過去問の使い方記事も参照してください。"
        ),
        "revision_note": "2026-06-18: GSC Phase5（archived past-questions-by-year/latest-year 統合）",
    },
    "syllabus-how-to-read": {
        "faq_4_question": "法改正や出題範囲の変更は過去問にどう反映しますか？",
        "faq_4_answer": (
            "要項の差分を先に1枚にまとめ、影響の大きい論点だけ週次演習へ優先配置します。"
            "例えば7/5（日）に前年度要項と比較し「出題範囲·注意事項·制度名」の3点差分→7/12（日）に該当分野演習15問、"
            "過去問は条文・制度が現行と一致する設問を優先し、旧制度の肢は要項注記と照合して除外します"
            "（旧「法改正の影響」「出題範囲と過去問」記事の要点を統合）。"
        ),
        "revision_note": "2026-06-18: GSC Phase5（archived legal-revision-impact/scope-vs-past-questions 統合）",
    },
}
