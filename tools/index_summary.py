#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""一覧表（用語・比較・早見・誤答）向けの記事要約文を、詳細記事フィールドから生成する。"""

from __future__ import annotations

import json
import re
from typing import Any

from tools.editorial_quality import EDITORIAL_GENERIC_PHRASES

INDEX_SUMMARY_MAX = 160

_BOILERPLATE_MARKERS: tuple[str, ...] = (
    "主体の取り違え・手順の前後逆・数値の単独暗記・記録省略",
    "4型に分けて整理",
    "5軸で違いを比較",
    "代表数値・条件・記録要件を",
    "で押さえる",
    "義務主体を先に固定し、比較表で整理",
    "職場フロー（事前確認→実施→記録→報告）",
    "過去問の逆転肢・数値混同を型別に分類",
    "法令条文とガイドライン・通知の対応表を作成",
    "関連制度との違いを横断マップにまとめ",
    "借地借家法・賃管法・受託契約の関係を整理します",
    "の基礎整理として主体・手続・数値を表で整理",
    "として主体・手続・数値を表で整理",
    "法定24時間義務なし",
)

_GLOSSARY_SKIP_SENTENCES: tuple[str, ...] = (
    "出題頻度が高い用語",
    "根拠条文と関連語との違いまでセット",
    "意味だけでなく",
    "試験では場面を想像",
    "押さえておきたい用語",
    "という意味です。賃貸住宅管理業法",
    "を整理する際に使われます",
)

_GENERIC_SNIPPET_SUFFIXES: tuple[str, ...] = (
    "に関わる用語です。",
    "を整理する際に使われます。",
    "と関係します。",
    "を確認します。",
    "を確認するために使われます。",
    "を考える場面で出てきます。",
    "につながる経営課題として捉えます。",
    "を説明する際に使われます。",
    "を検討します。",
)

_BOILER_TAIL = re.compile(
    r"数値・日程・合格基準は一般社団法人賃貸不動産経営管理士協議会[^。]*。?"
)
_LEAD_DEFINITION_RE = re.compile(r"^「[^」]+」は、[^。]+という意味です。?$")
_ANGLE_SUFFIX_RE = re.compile(r"（(?:基礎整理|実務連動|試験頻出|判例・ガイド|横断総合)）$")
_GENERIC_HIGHLIGHTS = frozenset({"代表値は要項・法令で確認", "要項・法令で確認"})

_SKIP_PARA_PREFIXES = ("特に「", "根拠は", "試験では、", "制度の内容は", "「")
_SKIP_PARA_CONTAINS = ("とセットで問われる", "選択肢を読むときは", "条文番号と定義のキーワード")


def _norm(value: object) -> str:
    return str(value or "").strip()


def split_sentences(text: str) -> list[str]:
    text = re.sub(r"\s+", " ", _norm(text))
    if not text:
        return []
    return [p.strip() for p in re.findall(r"[^。！？]+[。！？]?", text) if p.strip()]


def _clip_prose(text: str, *, limit: int = INDEX_SUMMARY_MAX) -> str:
    text = re.sub(r"\s+", " ", _norm(text))
    if not text:
        return ""
    if len(text) <= limit:
        return text if text.endswith(("。", "！", "？")) else f"{text.rstrip('。')}。"
    clipped = text[: limit - 1]
    for sep in ("。", "、", " "):
        idx = clipped.rfind(sep)
        if idx >= limit // 2:
            clipped = clipped[:idx]
            break
    return clipped.rstrip("、 ") + "…"


def _sentence_is_generic(sentence: str) -> bool:
    s = _norm(sentence)
    if not s or len(s) < 10:
        return True
    if any(m in s for m in _BOILERPLATE_MARKERS):
        return True
    if any(m in s for m in _GLOSSARY_SKIP_SENTENCES):
        return True
    if any(m in s for m in EDITORIAL_GENERIC_PHRASES):
        return True
    if s.endswith("を整理します。") and "「" in s and len(s) < 90:
        return True
    return False


def is_boilerplate_overview(text: str) -> bool:
    t = _norm(text)
    if not t:
        return True
    if any(m in t for m in _BOILERPLATE_MARKERS):
        return True
    if re.match(r"^「.+」（.+）で出やすい誤答を、", t):
        return True
    if re.match(r"^「.+」で押さえる", t):
        return True
    if t.endswith("を整理します。") or t.endswith("を整理します"):
        return True
    if "整理します。" in t and "数値は年度・条文で変わる" in t:
        return True
    if "の関係を整理" in t and len(t) < 90:
        return True
    if re.match(r"^.+（.+）として.+の関係を整理", t):
        return True
    return False


def _clean_hub_title(title: str) -> str:
    return _ANGLE_SUFFIX_RE.sub("", _norm(title))


def is_generic_hub_summary(text: str) -> bool:
    return is_boilerplate_overview(text)


def _meaningful_sentences(text: str, *, max_sentences: int = 2) -> list[str]:
    out: list[str] = []
    for s in split_sentences(_BOILER_TAIL.sub("", text)):
        if _sentence_is_generic(s):
            continue
        out.append(s if s.endswith(("。", "！", "？")) else f"{s}。")
        if len(out) >= max_sentences:
            break
    return out


def _split_semicolon(raw: str) -> list[str]:
    return [x.strip() for x in re.split(r"[;；]", raw or "") if x.strip()]


def _substantive_paragraphs(text: str) -> list[str]:
    paras = [p.strip() for p in re.split(r"\n\n+", text or "") if p.strip()]
    out: list[str] = []
    for p in paras:
        if any(p.startswith(prefix) for prefix in _SKIP_PARA_PREFIXES):
            continue
        if any(marker in p for marker in _SKIP_PARA_CONTAINS):
            continue
        if len(p) < 18:
            continue
        out.append(p)
    return out


def _parse_json_rows(entry: dict[str, Any], *keys: str) -> list[dict[str, Any]]:
    for key in keys:
        raw = entry.get(key)
        if isinstance(raw, list):
            return [r for r in raw if isinstance(r, dict)]
        if isinstance(raw, str) and raw.strip():
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if isinstance(data, list):
                return [r for r in data if isinstance(r, dict)]
    return []


def _is_generic_glossary_snippet(text: str, term: str) -> bool:
    t = _norm(text)
    if not t:
        return True
    if term and t.startswith(term) and any(t.endswith(s) for s in _GENERIC_SNIPPET_SUFFIXES):
        return True
    return _sentence_is_generic(t)


def glossary_index_snippet(entry: dict[str, Any]) -> str:
    """用語一覧「定義」列：詳細記事本文から要約。"""
    term = _norm(entry.get("term"))
    parts: list[str] = []

    paras = _substantive_paragraphs(_norm(entry.get("term_detail_body")))
    if paras:
        for s in _meaningful_sentences(paras[0], max_sentences=2):
            parts.append(s)

    if not parts:
        for s in split_sentences(_BOILER_TAIL.sub("", _norm(entry.get("article_lead")))):
            if _LEAD_DEFINITION_RE.match(s):
                continue
            if _sentence_is_generic(s):
                continue
            parts.append(s if s.endswith(("。", "！", "？")) else f"{s}。")
            if len(parts) >= 2:
                break

    if not parts:
        definition = _norm(entry.get("definition"))
        if definition and not _is_generic_glossary_snippet(definition, term):
            for s in _meaningful_sentences(definition, max_sentences=1):
                parts.append(s)

    if not parts:
        short = _norm(entry.get("short_def")).rstrip("。")
        if short:
            parts.append(short if short.startswith(term) else f"{term}は、{short}。")

    if not parts:
        exam = _split_semicolon(_norm(entry.get("exam_points")))
        if exam:
            parts.append(f"{term}は、{exam[0]}。" if term else f"{exam[0]}。")

    text = "".join(parts[:2])
    if term and text.startswith(f"「{term}」"):
        text = text[len(f"「{term}」") :].lstrip("は、").strip()
        if text and not text.startswith(term):
            text = f"{term}は、{text}"
    return _clip_prose(text)


def glossary_index_definition(entry: dict[str, Any]) -> str:
    return glossary_index_snippet(entry)


def _compare_overview_from_matrix(entry: dict[str, Any]) -> str:
    labels = entry.get("col_labels") or []
    if isinstance(labels, str):
        labels = _split_semicolon(labels)
    rows = _parse_json_rows(entry, "compare_rows")
    if len(labels) < 2 or not rows:
        return ""

    l1, l2 = labels[0], labels[1]
    bits: list[str] = []
    for row in rows[:4]:
        axis = _norm(row.get("axis"))
        cols = row.get("cols") or []
        if len(cols) < 2:
            continue
        c1, c2 = _norm(cols[0]), _norm(cols[1])
        if not c1 or not c2 or c1 == c2:
            continue
        if axis:
            bits.append(f"{axis}は{l1}が{c1.rstrip('。')}・{l2}が{c2.rstrip('。')}")
        else:
            bits.append(f"{l1}は{c1.rstrip('。')}、{l2}は{c2.rstrip('。')}")
        if len(bits) >= 2:
            break
    return "。".join(bits) + "。" if bits else ""


def compare_index_overview(entry: dict[str, Any]) -> str:
    parts: list[str] = []
    lead = _norm(entry.get("article_lead"))
    if lead and not is_boilerplate_overview(lead):
        parts.extend(_meaningful_sentences(lead, max_sentences=2))

    matrix = _compare_overview_from_matrix(entry)
    if matrix and matrix not in "".join(parts):
        parts.append(matrix)

    if not parts:
        exam = _split_semicolon(_norm(entry.get("exam_points")))
        if exam:
            parts.append(f"試験では{exam[0]}。")

    summary = _norm(entry.get("summary"))
    if not parts and summary and not is_boilerplate_overview(summary):
        parts.append(summary if summary.endswith("。") else f"{summary}。")

    return _clip_prose("".join(parts[:2]))


def _numbers_overview_from_items(entry: dict[str, Any]) -> str:
    title = _clean_hub_title(_norm(entry.get("title")))
    highlight = _norm(entry.get("highlight"))
    items = _parse_json_rows(entry, "detail_rows", "item_rows")
    parts: list[str] = []

    if highlight and highlight not in _GENERIC_HIGHLIGHTS and "要項" not in highlight:
        if title and title not in highlight:
            parts.append(f"{title}の早見では、{highlight.rstrip('。')}。")
        else:
            parts.append(highlight if highlight.endswith("。") else f"{highlight}。")

    for row in items[:3]:
        item = _norm(row.get("item"))
        value = _norm(row.get("value"))
        note = _norm(row.get("note"))
        if not item or not value or item in ("根拠", "確認", "試験") or any(
            x in value for x in ("要項", "法令で確認", "混同肢", "用語集")
        ):
            continue
        line = f"{item}は{value.rstrip('。')}"
        if note and len(note) <= 24 and note not in ("試験頻出", "条文確認", "正誤確認", "最新要項", "適用範囲"):
            line += f"（{note.rstrip('。')}）"
        parts.append(line + "。")
        if len(parts) >= 2:
            break
    return "".join(parts)


def numbers_index_overview(entry: dict[str, Any]) -> str:
    parts: list[str] = []
    lead = _norm(entry.get("article_lead"))
    if lead and not is_boilerplate_overview(lead):
        parts.extend(_meaningful_sentences(lead, max_sentences=2))

    item_text = _numbers_overview_from_items(entry)
    if item_text and item_text not in "".join(parts):
        parts.append(item_text)

    if not parts:
        exam = _split_semicolon(_norm(entry.get("exam_points")))
        if exam:
            parts.append(f"早見の要点は{exam[0]}。")

    summary = _norm(entry.get("summary"))
    if not parts and summary and not is_boilerplate_overview(summary):
        parts.append(summary if summary.endswith("。") else f"{summary}。")
    return _clip_prose("".join(parts[:2]))


def _clean_pattern_phrase(text: str, *, limit: int = 48) -> str:
    s = _norm(text).strip("「」\"'")
    if len(s) > limit:
        s = s[: limit - 1].rstrip("、 ") + "…"
    return s


def _mistake_overview_from_patterns(entry: dict[str, Any]) -> str:
    rows = _parse_json_rows(entry, "detail_rows", "pattern_rows")
    bits: list[str] = []
    confusion = _norm(entry.get("confusion_point"))
    if confusion and not _sentence_is_generic(confusion):
        bits.append(confusion if confusion.endswith("。") else f"{confusion}。")

    for row in rows[:2]:
        topic = _norm(row.get("topic"))
        wrong = _clean_pattern_phrase(_norm(row.get("wrong")))
        correct = _clean_pattern_phrase(_norm(row.get("correct")))
        if not wrong or not correct:
            continue
        if topic and topic not in wrong and len(wrong) <= 40:
            bits.append(f"{topic}で誤「{wrong}」→正「{correct}」。")
        else:
            bits.append(f"誤答は{wrong.rstrip('。')}。正しくは{correct.rstrip('。')}。")

    mistakes = _split_semicolon(_norm(entry.get("common_mistakes")))
    for m in mistakes[:1]:
        if m and m not in confusion and len(m) >= 6:
            bits.append(f"典型誤答は{m.rstrip('。')}。")
    return "".join(bits[:3])


def mistakes_index_overview(entry: dict[str, Any]) -> str:
    parts: list[str] = []
    lead = _norm(entry.get("article_lead"))
    if lead and not is_boilerplate_overview(lead):
        parts.extend(_meaningful_sentences(lead, max_sentences=2))

    pattern_text = _mistake_overview_from_patterns(entry)
    if pattern_text and pattern_text not in "".join(parts):
        parts.append(pattern_text)

    summary = _norm(entry.get("summary"))
    if not parts and summary and not is_boilerplate_overview(summary):
        parts.append(summary if summary.endswith("。") else f"{summary}。")

    title = _clean_hub_title(_norm(entry.get("title")))
    if not parts and title:
        parts.append(f"{title}で出やすい混同・逆転肢を表で整理した記事です。")
    return _clip_prose("".join(parts[:2]))


def hub_index_overview(entry: dict[str, Any], hub_type: str) -> str:
    if hub_type == "compare":
        return compare_index_overview(entry)
    if hub_type == "numbers":
        return numbers_index_overview(entry)
    if hub_type == "mistakes":
        return mistakes_index_overview(entry)
    return _clip_prose(_norm(entry.get("summary") or entry.get("article_lead")))
