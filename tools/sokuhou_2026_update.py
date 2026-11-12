#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
令和8年度(2026年) 賃貸不動産経営管理士試験 解答速報
TAC(資格の学校TAC)の解答速報ページをクロールし、
解答が公開されていれば kaitou-sokuhou/2026/index.html に反映する。

使い方:
  python3 tools/sokuhou_2026_update.py --check
      TACページを取得して公開状況を表示するだけ(ファイルは変更しない)。
      公開済み(45問以上に正答番号あり)なら終了コード0、未公開なら2。

  python3 tools/sokuhou_2026_update.py --apply
      公開済みなら kaitou-sokuhou/2026/index.html を書き換える。
      TACのHTMLスナップショットを tools/snapshots/ に保存する。
      異常値(没問・複数正解など)があれば "REVIEW REQUIRED" を表示し終了コード3。
      未公開なら何もせず終了コード2。
      既に反映済み(JSONが埋まっている)なら何もせず終了コード0。

このスクリプトはページを書き換える「下書き」を作るだけで、公開(マージ)はしない。
必ず人間が差分を確認してから公開すること。
"""
import argparse
import datetime
import html
import json
import os
import re
import subprocess
import sys

TAC_URL = "https://www.tac-school.co.jp/kouza_chintai/sokuhou.html"
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(REPO_ROOT, "kaitou-sokuhou", "2026", "index.html")
SNAP_DIR = os.path.join(REPO_ROOT, "tools", "snapshots")

TOTAL_Q = 50
PUBLISHED_THRESHOLD = 45  # これ以上の問に 1〜4 の数字が入っていたら「公開済み」とみなす

# 反映前(準備中)のページにある、置き換え対象の既存文字列 ----------------------
ANSWER_NOTE_PENDING = (
    '<p class="sokuhou-answer-note">自己採点用の参考解答です。公式の正解ではありません。</p>'
    '<p class="sokuhou-notice" id="sokuhou-answers-pending">現在、解答は準備中です。'
    '2026年11月15日（日）の試験終了後、問1〜問50の参考解答が判明し次第この欄に掲載します。</p>'
)
JSON_EMPTY = '<script type="application/json" id="sokuhou-answers">[]</script>'
META_DATE_OLD = "最終更新日：2026-11-10"
QUALITY_DATE_OLD = "<th>最終更新日</th><td>2026-11-10</td>"


def fetch(url):
    """curl(プロキシ設定済み)でHTMLを取得して文字列で返す。"""
    try:
        out = subprocess.run(
            ["curl", "-sS", "-L", "--max-time", "60", url],
            capture_output=True, timeout=90,
        )
        if out.returncode != 0:
            sys.stderr.write("curl failed: " + out.stderr.decode("utf-8", "replace") + "\n")
            return None
        return out.stdout.decode("utf-8", "replace")
    except Exception as e:  # noqa
        sys.stderr.write("fetch error: %r\n" % e)
        return None


def parse_meta(t):
    """公開予定日時 / 更新日時 / 次の更新予定 を抽出。"""
    meta = {}
    for m in re.finditer(
        r'<p>(公開予定日時|更新日時|次の更新予定)</p>\s*</div>\s*'
        r'<p class="DTLcontentList__text">(.*?)</p>', t, re.S):
        label = m.group(1)
        val = html.unescape(re.sub(r'<[^>]+>', '', m.group(2))).strip()
        meta[label] = val
    return meta


def parse_answers(t):
    """問1〜問50の (番号, 正答セルの生テキスト) を dict で返す。"""
    pairs = re.findall(
        r'<div class="cell question">\s*問\s*(\d+)\s*</div>\s*'
        r'<div class="cell answer">\s*(.*?)\s*</div>', t, re.S)
    vals = {}
    for n, a in pairs:
        txt = html.unescape(re.sub(r'<[^>]+>', '', a)).strip()
        vals[int(n)] = txt
    return vals


UNPUB_TOKENS = {"ー", "―", "−", "—", "-", "–", "", "？", "?"}


def classify(raw):
    """正答セルの値を分類して (kind, value) を返す。
    kind: 'num'(1〜4) / 'unpub'(未公開) / 'allcorrect'(没問・全員正解) / 'special'(要確認)
    """
    v = raw.strip()
    if re.fullmatch(r'[1-4]', v):
        return ("num", int(v))
    if v in UNPUB_TOKENS:
        return ("unpub", None)
    # 没問・全員正解・正解なし など → 全員正解扱い
    if re.search(r'(没問|全員正解|全て正解|すべて正解|正解なし|全選択肢)', v):
        return ("allcorrect", v)
    # 複数正解(例: 1・3, 1,3, 1/3)や想定外の値 → 要確認
    return ("special", v)


def build_records(vals):
    """JSON用レコードと、表示用・異常フラグを作る。"""
    records = []
    anomalies = []
    for no in range(1, TOTAL_Q + 1):
        raw = vals.get(no, "")
        kind, value = classify(raw)
        rec = {"no": no, "label": "問%d" % no, "points": 1, "choices": 4, "field": ""}
        if kind == "num":
            rec["correct"] = value
            disp = str(value)
        elif kind == "allcorrect":
            rec["correct"] = "-"
            rec["allCorrect"] = True
            disp = "※"
            anomalies.append("問%d: 全員正解扱い (TAC表記: %r)" % (no, raw))
        elif kind == "special":
            # 要確認。暫定で全員正解扱いにして自己採点が壊れないようにするが、必ず人間が確認する。
            rec["correct"] = "-"
            rec["allCorrect"] = True
            rec["_raw"] = raw
            disp = "※"
            anomalies.append("問%d: 想定外の値 %r (複数正解の可能性・要確認)" % (no, raw))
        else:  # unpub
            rec["correct"] = None
            disp = "ー"
            anomalies.append("問%d: 未公開(ー)" % no)
        rec["_disp"] = disp
        records.append(rec)
    return records, anomalies


def count_published(vals):
    return sum(1 for no in range(1, TOTAL_Q + 1)
              if classify(vals.get(no, ""))[0] == "num")


def answer_table_html(records, update_text):
    """2025年ページと同じ体裁の解答一覧テーブルを生成。"""
    note = (
        '<p class="sokuhou-answer-note">資格の学校TACが公開した'
        '<a href="%s" target="_blank" rel="noopener noreferrer">解答速報</a>'
        'に基づく参考解答です（TAC %s 時点）。公式の正解ではありません。</p>'
        % (TAC_URL, html.escape(update_text or ""))
    )
    rows = []
    for start in range(1, TOTAL_Q + 1, 10):
        end = start + 9
        cells = []
        for no in range(start, end + 1):
            rec = records[no - 1]
            cells.append('<span class="sokuhou-ans-pair">問%d<b>%s</b></span>'
                         % (no, rec["_disp"]))
        rows.append('<tr><th>問%d〜問%d</th><td>%s</td></tr>'
                    % (start, end, "".join(cells)))
    table = (
        '<table class="seo-info-table sokuhou-ans-table"><thead><tr><th>問</th>'
        '<th>解答</th></tr></thead><tbody>%s</tbody></table>' % "".join(rows)
    )
    has_star = any(r["_disp"] == "※" for r in records)
    foot = ""
    if has_star:
        foot = ('<p class="sokuhou-answer-note">※ は出題団体の判断等により'
                '複数正解・全員正解として扱われた可能性がある問題です。'
                '最新情報は公式およびTACの解答速報でご確認ください。</p>')
    return note + table + foot


def records_to_json(records):
    clean = []
    for r in records:
        d = {"no": r["no"], "label": r["label"], "correct": r["correct"],
             "points": r["points"], "choices": r["choices"]}
        if r.get("allCorrect"):
            d["allCorrect"] = True
        d["field"] = ""
        clean.append(d)
    return json.dumps(clean, ensure_ascii=False)


def save_snapshot(raw, meta, vals):
    os.makedirs(SNAP_DIR, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    with open(os.path.join(SNAP_DIR, "tac-sokuhou-%s.html" % stamp), "w",
              encoding="utf-8") as f:
        f.write(raw)
    summary = {
        "fetched_at": stamp,
        "meta": meta,
        "answers": {str(n): vals.get(n, "") for n in range(1, TOTAL_Q + 1)},
        "published_count": count_published(vals),
    }
    with open(os.path.join(SNAP_DIR, "tac-sokuhou-%s.json" % stamp), "w",
              encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    return stamp


def apply_to_page(records, update_text):
    with open(TARGET, encoding="utf-8") as f:
        src = f.read()

    if JSON_EMPTY not in src:
        if '"correct"' in src and 'id="sokuhou-answers"' in src:
            return ("already", "既に解答が反映済みです（sokuhou-answers が埋まっています）。")
        return ("error", "想定した空のJSON(sokuhou-answers)が見つかりません。ページ構造が変わった可能性があります。")
    if ANSWER_NOTE_PENDING not in src:
        return ("error", "想定した準備中テキストが見つかりません。ページ構造が変わった可能性があります。")

    today = datetime.date.today().isoformat()
    new = src.replace(ANSWER_NOTE_PENDING, answer_table_html(records, update_text))
    new = new.replace(JSON_EMPTY,
                      '<script type="application/json" id="sokuhou-answers">%s</script>'
                      % records_to_json(records))
    new = new.replace(META_DATE_OLD, "最終更新日：%s" % today)
    new = new.replace(QUALITY_DATE_OLD, "<th>最終更新日</th><td>%s</td>" % today)

    with open(TARGET, "w", encoding="utf-8") as f:
        f.write(new)
    return ("ok", "反映しました。最終更新日: %s" % today)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.check or args.apply):
        ap.error("--check か --apply を指定してください")

    raw = fetch(TAC_URL)
    if raw is None:
        print("FETCH FAILED: TACページを取得できませんでした。ネットワーク許可とプロキシを確認してください。")
        sys.exit(4)

    meta = parse_meta(raw)
    vals = parse_answers(raw)
    pub = count_published(vals)
    update_text = meta.get("更新日時", "")

    print("=== TAC解答速報 取得結果 ===")
    print("公開予定日時 :", meta.get("公開予定日時", "(なし)"))
    print("更新日時     :", meta.get("更新日時", "(なし)"))
    print("次の更新予定 :", meta.get("次の更新予定", "(なし)"))
    print("パースできた問数 :", len(vals))
    print("正答番号が入っている問数 :", pub, "/", TOTAL_Q)
    print("正答(生値) :", " ".join("%d:%s" % (n, vals.get(n, "")) for n in range(1, TOTAL_Q + 1)))

    published = pub >= PUBLISHED_THRESHOLD

    if args.check:
        if published:
            print("STATUS: PUBLISHED (公開済み)")
            sys.exit(0)
        else:
            print("STATUS: NOT PUBLISHED (未公開)")
            sys.exit(2)

    # --apply
    stamp = save_snapshot(raw, meta, vals)
    print("スナップショット保存:", stamp)
    if not published:
        print("STATUS: NOT PUBLISHED — ページは変更しませんでした。")
        sys.exit(2)

    records, anomalies = build_records(vals)
    status, msg = apply_to_page(records, update_text)
    print("APPLY:", status, "-", msg)

    # 合格推定点(あれば)を参考表示
    mm = re.search(r'合格推定点', raw)
    if mm:
        around = html.unescape(re.sub(r'<[^>]+>', ' ', raw[mm.start():mm.start() + 400]))
        around = re.sub(r'\s+', ' ', around).strip()
        print("参考(合格推定点まわり):", around[:200])

    if anomalies:
        print("---- REVIEW REQUIRED (要確認) ----")
        for a in anomalies:
            print(" *", a)

    if status == "error":
        sys.exit(5)
    if anomalies and any("想定外" in a or "未公開" in a for a in anomalies):
        sys.exit(3)
    sys.exit(0)


if __name__ == "__main__":
    main()
