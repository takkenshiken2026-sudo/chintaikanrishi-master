#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BATCH_DIR = ROOT / "data" / "glossary_handcraft_batches"
OUT_DIR = ROOT / "data" / "glossary_handcraft_content"

BATCH_FILES = [
    "賃貸住宅管理業法.json",
    "関連法令.json",
    "賃貸経営・PM_AM.json",
]


def clean_list(value: str) -> list[str]:
    return [v.strip() for v in (value or "").split(";") if v.strip()]


def make_entry(item: dict[str, str], index: int) -> dict[str, str]:
    term = (item.get("term") or "").strip()
    short_def = (item.get("short_def") or "").strip()
    definition = (item.get("definition") or "").strip()
    legal_basis = (item.get("legal_basis") or "").strip() or "関連法令・契約条項"
    related_terms = clean_list(item.get("related_terms") or "")
    related_a = related_terms[0] if related_terms else "関連制度"
    related_b = related_terms[1] if len(related_terms) > 1 else "近接概念"
    category = (item.get("category") or "").strip()

    lead_patterns = [
        f"「{term}」は{category}分野で頻出です。定義を暗記するだけでなく、出題文で言い換えられたときに判断できるよう、根拠と合わせて整理しましょう。",
        f"{term}は、試験で引っかけ肢が作られやすい論点です。{short_def}という軸を先に押さえると、誤肢を落としやすくなります。",
        f"{term}を得点源にするには、本文のキーワードを条文・実務のどちらにもつなげて覚えるのが近道です。まずは定義と周辺語の違いを確認してください。",
    ]

    body_patterns = [
        (
            f"{definition}\n\n"
            f"試験では「{term}の要件・効果を正しく言えるか」がそのまま得点差になります。"
            f"とくに結論だけでなく、前提条件や例外の語句まで拾って読むのがコツです。"
        ),
        (
            f"{definition}\n\n"
            f"この用語は、{related_a}と並べて問われることが多いです。"
            f"「何が同じで、何が違うか」を1行で説明できる状態にしておくと、選択肢問題で迷いにくくなります。"
        ),
        (
            f"{definition}\n\n"
            f"実務では手続の順番や主体の違いでトラブルが生じやすいため、"
            f"試験でも時系列・当事者・効果の3点セットで確認する出題が目立ちます。"
        ),
    ]

    exam_points_patterns = [
        f"{term}の定義語句（主体・要件・効果）を、そのまま再現できるようにする",
        f"{legal_basis}を根拠に、誤った言い換え肢を除外できるようにする",
        f"{related_a}と{related_b}との違いを、1分で説明できるようにする",
    ]

    common_patterns = [
        f"「{term}」では、用語名の印象だけで判断してしまい、要件の一部を落とす誤りが頻出です。先に定義文を分解してから肢を読むと防げます。",
        f"{term}は、{related_a}との混同が典型ミスです。主語（誰の義務か）と効果（何が起きるか）を分けて覚えてください。",
        f"条文番号や手続時期を曖昧にしたまま解くと失点しやすい論点です。定義→根拠→適用場面の順で確認しましょう。",
    ]

    memory_patterns = [
        f"{term}：{legal_basis}／対比：{related_a}",
        f"{term}＝「{short_def.rstrip('。')}」を先に固定",
        f"{term}は主体・時期・効果の3語で暗記",
    ]

    focus_patterns = [
        f"「{term}」は、定義中の要件語と効果語が一致しているかを最優先で確認すると正答率が上がります。",
        f"{term}の問題は、{related_a}との差分に注目して消去法を使うと安定します。",
        f"まず{legal_basis}との対応を見て、その後に定義の例外・限定語を確認する順で読むのが有効です。",
    ]

    summary = short_def if short_def else definition.split("。")[0] + "。"

    faq1_q = f"{term}とは何ですか？"
    faq1_a = f"{summary}根拠は主に{legal_basis}です。"

    faq2_q = f"{term}で試験に出やすいポイントは？"
    faq2_a = (
        f"定義語句の正確さと、{related_a}との違いが頻出です。"
        "肢の主語・時期・効果が定義と一致しているかを確認してください。"
    )

    faq3_q = f"{term}の覚え方のコツは？"
    faq3_a = (
        f"「{short_def.rstrip('。')}」を起点に、"
        f"根拠（{legal_basis}）と対比語（{related_a}）を1セットで復習すると定着しやすいです。"
    )

    return {
        "article_title": f"{term}とは？意味・試験ポイントを整理",
        "article_lead": lead_patterns[index % len(lead_patterns)],
        "term_detail_body": body_patterns[index % len(body_patterns)],
        "exam_points": ";".join(exam_points_patterns),
        "exam_focus": focus_patterns[index % len(focus_patterns)],
        "summary_body": summary,
        "common_mistakes": common_patterns[index % len(common_patterns)],
        "memory_tip": memory_patterns[index % len(memory_patterns)],
        "explanation": f"{term}とは、{short_def.rstrip('。')}。試験では定義と根拠の対応整理が重要です。",
        "faq_1_question": faq1_q,
        "faq_1_answer": faq1_a,
        "faq_2_question": faq2_q,
        "faq_2_answer": faq2_a,
        "faq_3_question": faq3_q,
        "faq_3_answer": faq3_a,
    }


def build_file(batch_name: str) -> tuple[str, int]:
    src = BATCH_DIR / batch_name
    if not src.exists():
        raise FileNotFoundError(f"Batch file not found: {src}")
    data = json.loads(src.read_text(encoding="utf-8"))
    result: dict[str, dict[str, str]] = {}
    for idx, item in enumerate(data):
        term = (item.get("term") or "").strip()
        if not term:
            continue
        result[term] = make_entry(item, idx)
    out = OUT_DIR / batch_name
    out.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return batch_name, len(result)


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    counts: list[tuple[str, int]] = []
    for name in BATCH_FILES:
        counts.append(build_file(name))
    for name, count in counts:
        print(f"{name}\t{count}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
