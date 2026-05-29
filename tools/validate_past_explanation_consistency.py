#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""過去問 CSV の正答と解説（生成 HTML 含む）の整合性を検証する。"""

from __future__ import annotations

import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.build_past_question_pages import page_dict
from tools.enrich_past_explanation_choices import stem_asks_inappropriate, stem_asks_most_correct
from tools.q_explanation import (
    build_explanation_html,
    norm,
    parse_explanation_choices,
    question_ask_mode,
)

DATA_CSV = ROOT / "data" / "past_questions.csv"

CONFUSING_PATTERNS = (
    r"解説の要点：",
    r"それと矛盾します",
    r"参照用の○×判定",
)


def parse_correct(raw: object) -> int | None:
    s = norm(raw)
    if not s:
        return None
    try:
        return int(s)
    except ValueError:
        return None


class ConsistencyValidator:
    def __init__(self) -> None:
        self.errors: list[str] = []

    def error(self, year: int | str, qno: int | str, msg: str) -> None:
        self.errors.append(f"{year}-{int(qno):02d}: {msg}")

    def validate_row(self, row: dict, line_no: int) -> None:
        try:
            page = page_dict(row, line_no)
        except ValueError as exc:
            self.error("?", line_no, str(exc))
            return

        cor = page.get("correct")
        if page.get("is_invalidated") or cor is None:
            return

        year, qno = page["year"], page["qno"]
        mode = question_ask_mode(page["stem_plain"])
        stem = norm(row.get("stem"))

        exp = norm(row.get("explanation"))
        m = re.search(r"正解は\s*(\d+)", exp)
        if m and int(m.group(1)) != cor:
            self.error(year, qno, f"explanation の正解番号 ({m.group(1)}) ≠ correct ({cor})")

        parsed = parse_explanation_choices(norm(row.get("explanation_choices")))
        if cor in parsed:
            self.error(year, qno, f"explanation_choices に正答肢 ({cor}) が含まれています")

        for field, name in (
            (norm(row.get("explanation_correct")), "explanation_correct"),
            (norm(row.get("explanation_summary")), "explanation_summary"),
        ):
            if not field:
                continue
            if mode == "most_correct" and re.search(
                rf"選択肢{cor}.*不適切|（{cor}）.*誤っ", field
            ):
                self.error(year, qno, f"{name} が正答 {cor} を誤り扱いしています")
            if mode == "least_appropriate" and re.search(
                rf"選択肢{cor}.*適切と整理|（{cor}）.*正しい記述", field
            ):
                self.error(year, qno, f"{name} が正答 {cor} を正しい扱いしています")

        html = build_explanation_html(page, row)
        if "q-exp-wrong-h" in html:
            wrong_part = html.split("q-exp-wrong-h", 1)[1]
            wrong_part = (
                wrong_part.split("q-exp-tip-h", 1)[0]
                if "q-exp-tip-h" in wrong_part
                else wrong_part
            )
            items = re.findall(
                r'q-exp-choice-num">（(\d+)）</span>.*?q-exp-choice-note">(.*?)</p>',
                wrong_part,
                re.S,
            )
            for num_s, note in items:
                n = int(num_s)
                if n == cor:
                    self.error(
                        year,
                        qno,
                        "生成 HTML の「他の選択肢」に正答肢が含まれています",
                    )
                    continue
                note_plain = re.sub(r"<[^>]+>", "", note)
                for pat in CONFUSING_PATTERNS:
                    if re.search(pat, note_plain):
                        self.error(
                            year,
                            qno,
                            f"他肢 ({n}) の解説に紛らわしい表現 ({pat}): {note_plain[:80]}…",
                        )
                        break
                if mode == "least_appropriate" and re.search(
                    rf"（{n}）.*(?:この記述は誤り|記述.*誤っ)", note_plain
                ) and "正答にはなりません" not in note_plain:
                    self.error(
                        year,
                        qno,
                        f"他肢 ({n}) を誤り扱い（least_appropriate では適切な記述のはず）",
                    )
                if mode == "most_correct" and re.search(
                    rf"（{n}）.*単体では適切", note_plain
                ):
                    self.error(
                        year,
                        qno,
                        f"他肢 ({n}) を適切扱い（most_correct では誤りのはず）",
                    )

        if stem_asks_inappropriate(stem) != (mode == "least_appropriate"):
            self.error(
                year,
                qno,
                f"設問形式の判定不一致: stem_asks_inappropriate vs question_ask_mode ({mode})",
            )

    def run(self) -> int:
        if not DATA_CSV.is_file():
            print(f"error: {DATA_CSV} not found", file=sys.stderr)
            return 1
        with DATA_CSV.open(encoding="utf-8-sig") as f:
            for line_no, row in enumerate(csv.DictReader(f), start=2):
                self.validate_row(row, line_no)
        if self.errors:
            print(f"validate_past_explanation_consistency: {len(self.errors)} error(s)")
            for e in self.errors[:50]:
                print("  ERROR:", e)
            if len(self.errors) > 50:
                print(f"  … and {len(self.errors) - 50} more")
            return 1
        print("validate_past_explanation_consistency: OK")
        return 0


def main() -> int:
    return ConsistencyValidator().run()


if __name__ == "__main__":
    raise SystemExit(main())
