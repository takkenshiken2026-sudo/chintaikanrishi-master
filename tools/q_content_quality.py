#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""過去問・実践・一問一答の品質判定（デモ行除外・一問一答 SEO・本文重複除去）。"""

from __future__ import annotations

import re

from tools.seo_utils import NOINDEX_ROBOTS_META

_ICHIMON_ID_NUMERIC = re.compile(r"^(\d{4})-(\d+)-(\d+)$")
_ICHIMON_ID_KANA = re.compile(r"^(\d{4}-\d+)-([アイウエオ])$")
_ICHIMON_ID_EXAM = re.compile(r"^(.+-\d+)-(\d+)$")
_ICHIMON_ID_JA = re.compile(r"^(.+_問\d+)_選択肢(\d+)$")
_KANA_BRANCH_ORDER = "アイウエオ"
_DEMO_STEM_RE = re.compile(
    r"Sample試験|テンプレートの使い方|生成済みJS|CSV.*build_all|列名は自由|ドメイン設定は不要"
)


def norm(value: object) -> str:
    return (value or "").strip() if value is not None else ""


def dedupe_prose(text: str) -> str:
    """段落・文の重複を除去（GSC 重複コンテンツ対策）。"""
    raw = norm(text)
    if not raw:
        return raw
    paras = [p.strip() for p in re.split(r"\n\s*\n", raw) if p.strip()]
    seen_para: set[str] = set()
    kept_paras: list[str] = []
    for para in paras:
        key = re.sub(r"\s+", "", para)
        if key in seen_para:
            continue
        seen_para.add(key)
        sents = re.split(r"(?<=[。！？!?])\s*", para)
        seen_sent: set[str] = set()
        kept_sents: list[str] = []
        for sent in sents:
            s = sent.strip()
            if not s:
                continue
            sk = re.sub(r"\s+", "", s)
            if sk in seen_sent:
                continue
            seen_sent.add(sk)
            kept_sents.append(s)
        if kept_sents:
            kept_paras.append("".join(kept_sents))
    return "\n\n".join(kept_paras)


def is_demo_past_question_row(
    row: dict[str, str],
    *,
    excluded_exam_years: set[str] | None = None,
) -> bool:
    wareki = norm(row.get("exam_wareki"))
    stem = norm(row.get("stem"))
    exam_year = norm(row.get("exam_year"))
    if excluded_exam_years and exam_year in excluded_exam_years:
        return True
    if "サンプル" in wareki:
        return True
    if _DEMO_STEM_RE.search(stem):
        return True
    return False


# --- 過去問ページの index/noindex 判定・解説サニタイズ ---------------------
# 過去問の解説（explanation / explanation_choices）は、自動生成された定型テンプレート
# が大半で、個別問題ごとの実質的な理由づけを含まない。テンプレートのみのページを大量に
# index させると「有用性の低いコンテンツ」（Google AdSense / 検索品質）の要因になるため、
# 固有の解説が執筆された行だけを index し、定型のままの行は noindex（サイト内演習用）とする。
#
# 判定は保守的（＝迷ったら noindex）。実践演習（explanation に固有の理由づけあり）と
# 用語・ガイド記事を index の正本とする方針。
_PAST_TEMPLATE_MARKERS = (
    "設問の条件に合う",
    "正解になるのは",
    "参照用の",
    "○×判定",
    "が示す論点と異なります",
    "組合せ問題では",
    "記述の正誤を先に確定",
    "単体では適切な記述",
    "この記述が設問",
    "設問の求める不適切な記述",
    "論点の基本整理に合っています",
    "設問の求める結論に合う",
    "全選択肢が正解扱い",
)

_PAST_CHOICE_NOTE_RE = re.compile(r"^\s*\d+\s*[:：]\s*(.*)$")


def _past_choices_are_identical(raw: str) -> bool:
    """explanation_choices（"2:…;3:…;4:…"）の各注記が番号違いだけの同一文なら True。"""
    notes: list[str] = []
    for part in re.split(r"[;；]", norm(raw)):
        m = _PAST_CHOICE_NOTE_RE.match(part)
        if m:
            body = re.sub(r"（\d+）|\d+|「[^」]*」", "", m.group(1))
            body = re.sub(r"\s+", "", body)
            if body:
                notes.append(body)
    return len(notes) >= 2 and len(set(notes)) == 1


def past_explanation_is_substantive(row: dict[str, str]) -> bool:
    """過去問の解説が定型テンプレートでなく、固有の理由づけを含むとき True。"""
    exp = norm(row.get("explanation"))
    if len(exp) < 120:
        return False
    if any(m in exp for m in _PAST_TEMPLATE_MARKERS):
        return False
    if _past_choices_are_identical(row.get("explanation_choices", "")):
        return False
    return True


def past_question_should_index(row: dict[str, str]) -> bool:
    """個別過去問ページを index してよいか。固有解説がある行のみ True。"""
    return past_explanation_is_substantive(row)


def sanitize_past_explanation_row(row: dict[str, str]) -> dict[str, str]:
    """表示前に過去問解説の循環論法（トートロジー）を取り除いた row のコピーを返す。

    - 「選択肢Nが正解になるのは、この記述が設問の条件に合う…だからです。」
    - 「参照用の○×判定でも選択肢Nは…と整理できます。」
    などの中身のない一文を除去し、番号違いだけの同一 explanation_choices は空にして
    ビルダー側のフォールバック（選択肢文からの案内）に委ねる。
    """
    out = dict(row)
    exp = norm(out.get("explanation"))
    if exp:
        exp = re.sub(
            r"選択肢\s*\d+\s*が正解になるのは、この記述が設問の条件に合う[^。]*。",
            "",
            exp,
        )
        exp = re.sub(r"参照用の○×判定でも[^。]*。", "", exp)
        exp = re.sub(r"設問の条件に合う肢かどうかを確認してください。?", "", exp)
        out["explanation"] = dedupe_prose(exp).strip()
    if _past_choices_are_identical(out.get("explanation_choices", "")):
        out["explanation_choices"] = ""
    return out


def is_demo_practice_question_row(row: dict[str, str]) -> bool:
    stem = norm(row.get("stem"))
    if _DEMO_STEM_RE.search(stem):
        return True
    c1 = norm(row.get("choice_1"))
    if "data/past_questions.csv" in c1 or "build_all.py" in c1:
        return True
    return False


_ichimon_primary_cache: set[str] | None = None


def ichimon_id_parts(row_id: str) -> tuple[int, int, int] | None:
    m = _ICHIMON_ID_NUMERIC.match(norm(row_id))
    if not m:
        return None
    return int(m.group(1)), int(m.group(2)), int(m.group(3))


def ichimon_group_branch(row_id: str) -> tuple[str, int] | None:
    """一問一答 ID から (元問キー, 枝番) を返す。単独ページは None。"""
    rid = norm(row_id)
    m = _ICHIMON_ID_NUMERIC.match(rid)
    if m:
        return f"{m.group(1)}-{m.group(2)}", int(m.group(3))
    m = _ICHIMON_ID_KANA.match(rid)
    if m:
        return m.group(1), _KANA_BRANCH_ORDER.index(m.group(2))
    m = _ICHIMON_ID_JA.match(rid)
    if m:
        return m.group(1), int(m.group(2))
    m = _ICHIMON_ID_EXAM.match(rid)
    if m:
        return m.group(1), int(m.group(2))
    return None


def build_ichimon_primary_ids(rows: list[dict[str, str]]) -> set[str]:
    """元問ごとに最小枝番のみ index（例: 2024-05-5 / 2704b-01-1 / 令和…_問38_選択肢1）。"""
    mins: dict[str, int] = {}
    for row in rows:
        gb = ichimon_group_branch(norm(row.get("id")))
        if gb is None:
            continue
        key, branch = gb
        mins[key] = min(branch, mins.get(key, branch))
    primary: set[str] = set()
    for row in rows:
        rid = norm(row.get("id"))
        gb = ichimon_group_branch(rid)
        if gb is None:
            primary.add(rid)
            continue
        key, branch = gb
        if mins.get(key) == branch:
            primary.add(rid)
    return primary


def set_ichimon_primary_ids(primary: set[str]) -> None:
    global _ichimon_primary_cache
    _ichimon_primary_cache = primary


def ichimon_is_primary_seo_row(row_id: str) -> bool:
    rid = norm(row_id)
    if _ichimon_primary_cache is not None:
        return rid in _ichimon_primary_cache
    parts = ichimon_id_parts(rid)
    if parts is None:
        return True
    _y, _q, c = parts
    return c == 1


def ichimon_robots_meta(row_id: str) -> str:
    """一問一答の個別ページはサイト内演習用。過去問・実践演習を index の正本とする。"""
    del row_id  # 枝番・y9000 を問わず個別 URL はすべて noindex
    return NOINDEX_ROBOTS_META


def ichimon_body_already_states_truth(body: str, *, is_true: bool) -> bool:
    b = norm(body)
    if not b:
        return False
    if is_true:
        return bool(re.search(r"正しい内容|正当である|適切である|○\s*が正答|答えは\s*○", b))
    return bool(re.search(r"誤り|誤った|不適切|×\s*が正答|答えは\s*×|正しくない", b))


def clean_ichimon_correct_body(
    correct_body: str,
    *,
    summary: str,
    is_true: bool,
) -> str:
    body = dedupe_prose(correct_body)
    sm = dedupe_prose(summary)
    if sm and body.startswith(sm):
        body = body[len(sm) :].lstrip("。、 \n")
    body = re.sub(
        r"^この記述は正しい内容です[。.]?\s*",
        "",
        body,
    )
    body = re.sub(
        r"^この記述は誤りです[。.]?\s*",
        "",
        body,
    )
    if ichimon_body_already_states_truth(body, is_true=is_true):
        body = re.sub(r"^[。.]\s*", "", body)
    return body.strip()


def strip_four_choice_leak(text: str) -> str:
    """一問一答用: 4択過去問インポート由来の「選択肢N」表現を除去・言い換え。"""
    t = norm(text)
    if not t:
        return t

    t = re.sub(
        r"^正解は\s*(?:選択肢\s*)?[（(]?\d+[）)]?\s*です[。.]?\s*",
        "",
        t,
    )
    t = re.sub(
        r"^正答は\s*(?:選択肢\s*)?[（(]?\d+[）)]?\s*です[。.]?\s*",
        "",
        t,
    )
    t = re.sub(
        r"正解は\s*(?:選択肢\s*)?[（(]?\d+[）)]?\s*です[。.]?",
        "",
        t,
    )
    t = re.sub(
        r"正答は\s*(?:選択肢\s*)?[（(]?\d+[）)]?\s*です[。.]?",
        "",
        t,
    )

    def _choice_quote_repl(m: re.Match[str]) -> str:
        quote = m.group(1).strip()
        if quote.endswith("..."):
            quote = quote[:-3].rstrip()
        return f"問題文は「{quote}」の趣旨どおりであり、制度の整理と一致します。"

    t = re.sub(
        r"選択肢\s*[（(]?\d+[）)]?\s*の[「「]([^」]+)[」」]という内容が結論に合います[。.]?",
        _choice_quote_repl,
        t,
    )
    t = re.sub(r"選択肢\s*[（(]?\d+[）)]?\s*の", "問題文の", t)
    t = re.sub(
        r"その他の記述は、主体・手続・期間・効果などの点でずれています[。.]?\s*",
        "",
        t,
    )
    return dedupe_prose(t.strip())
