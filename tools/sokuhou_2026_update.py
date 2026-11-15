#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
令和8年度(2026年) 賃貸不動産経営管理士試験 解答速報 反映ツール

各解答速報ページをクロールして判明分を集約し、
kaitou-sokuhou/2026/index.html に反映する。

データ方針:
  kaitou-sokuhou/2026/answers-known.json を「恒久ストア」とする。
  - 一度判明した解答はここに蓄積され、ライブ側から消えても逆戻りしない。
  - agaroot 等で新たに判明した問(数字)は、未登録なら蓄積する。
  - TAC が公表した問は最優先で上書き(訂正)する。
  - ストア既存値とライブ側が食い違う場合は上書きせず「要確認」で報告する。
  ページ(解答一覧・自己採点JSON)は常にこのストアから描画する。

クロール元:
  - TAC:     https://www.tac-school.co.jp/kouza_chintai/sokuhou.html   (最優先)
  - agaroot: https://www.agaroot.jp/chintai_kk/sokuho/

使い方:
  python3 tools/sokuhou_2026_update.py --check   # 取得・集約状況の表示のみ
  python3 tools/sokuhou_2026_update.py --apply   # ストア更新＋ページ反映(冪等)

このスクリプトはページを書き換えるだけで、本番公開(mainへのマージ)は呼び出し側で行う。
"""
import argparse
import datetime
import html
import json
import os
import re
import subprocess
import sys

SOURCES = [
    ("TAC", "https://www.tac-school.co.jp/kouza_chintai/sokuhou.html"),
    ("agaroot", "https://www.agaroot.jp/chintai_kk/sokuho/"),
]
TAC_URL = SOURCES[0][1]
AGAROOT_URL = SOURCES[1][1]

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TARGET = os.path.join(REPO_ROOT, "kaitou-sokuhou", "2026", "index.html")
KNOWN_JSON = os.path.join(REPO_ROOT, "kaitou-sokuhou", "2026", "answers-known.json")
SNAP_DIR = os.path.join(REPO_ROOT, "tools", "snapshots")

TOTAL_Q = 50
TAC_PUBLISHED_THRESHOLD = 45
UNPUB_TOKENS = {"ー", "―", "−", "—", "-", "–", "", "？", "?"}
ALLCORRECT_TOKEN = "没問"  # ストアに保存する全員正解マーカー


# --- 取得 ---------------------------------------------------------------
def fetch(url):
    try:
        out = subprocess.run(["curl", "-sS", "-L", "--max-time", "60", url],
                             capture_output=True, timeout=90)
        if out.returncode != 0:
            sys.stderr.write("curl failed(%s): %s\n" % (url, out.stderr.decode("utf-8", "replace")))
            return None
        return out.stdout.decode("utf-8", "replace")
    except Exception as e:  # noqa
        sys.stderr.write("fetch error(%s): %r\n" % (url, e))
        return None


def parse_tac_meta(t):
    meta = {}
    for m in re.finditer(
        r'<p>(公開予定日時|更新日時|次の更新予定)</p>\s*</div>\s*'
        r'<p class="DTLcontentList__text">(.*?)</p>', t, re.S):
        meta[m.group(1)] = html.unescape(re.sub(r'<[^>]+>', '', m.group(2))).strip()
    return meta


def parse_tac_answers(t):
    pairs = re.findall(
        r'<div class="cell question">\s*問\s*(\d+)\s*</div>\s*'
        r'<div class="cell answer">\s*(.*?)\s*</div>', t, re.S)
    return {int(n): html.unescape(re.sub(r'<[^>]+>', '', a)).strip() for n, a in pairs}


def parse_agaroot_answers(t):
    pairs = re.findall(
        r'<p class="head">\s*問\s*0?(\d+)\s*</p>\s*<p class="desc">(.*?)</p>', t, re.S)
    return {int(n): html.unescape(re.sub(r'<[^>]+>', '', a)).strip() for n, a in pairs}


def classify(raw):
    v = (raw or "").strip()
    if re.fullmatch(r'[1-4]', v):
        return ("num", int(v))
    if v in UNPUB_TOKENS:
        return ("unpub", None)
    if re.search(r'(没問|全員正解|全て正解|すべて正解|正解なし|全選択肢)', v):
        return ("allcorrect", v)
    return ("special", v)


# --- 恒久ストア ---------------------------------------------------------
def load_store():
    if not os.path.exists(KNOWN_JSON):
        return {}
    try:
        with open(KNOWN_JSON, encoding="utf-8") as f:
            data = json.load(f)
        return {int(k): v for k, v in data.get("answers", {}).items()}
    except Exception as e:  # noqa
        sys.stderr.write("store 読み込み失敗: %r\n" % e)
        return {}


def save_store(store):
    answers = {str(no): store[no] for no in sorted(store)}
    data = {
        "_comment": "2026年 解答速報の参考解答(自己採点用)。問番号→正答番号(1〜4)。"
                    "全員正解は \"没問\"。公式の正解ではありません。",
        "_updated": datetime.datetime.now().astimezone().strftime("%Y-%m-%dT%H:%M%z"),
        "answers": answers,
    }
    with open(KNOWN_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")


def ingest(store, tac_vals, aga_vals):
    """ライブ取得分をストアへ集約。戻り値 (changes, conflicts, flags)。
    - agaroot: 数字で未登録なら追加。既存と食い違えば conflict(上書きしない)。
    - TAC: 数字/没問は最優先で上書き。
    """
    changes, conflicts = [], []

    # agaroot(数字のみ自動蓄積)
    for no, raw in sorted(aga_vals.items()):
        k, v = classify(raw)
        if k == "num":
            if no not in store:
                store[no] = v
                changes.append("問%d=%d を追加(agaroot)" % (no, v))
            elif str(store[no]) != str(v):
                conflicts.append("問%d: 既存%s vs agaroot%s(ストア維持・要確認)"
                                 % (no, store[no], v))

    # TAC(最優先・上書き)
    for no, raw in sorted(tac_vals.items()):
        k, v = classify(raw)
        if k == "num":
            if store.get(no) != v:
                old = store.get(no)
                store[no] = v
                changes.append("問%d=%d をTACで確定%s"
                               % (no, v, ("(訂正:旧%s)" % old if old is not None else "")))
        elif k in ("allcorrect", "special"):
            if store.get(no) != ALLCORRECT_TOKEN:
                store[no] = ALLCORRECT_TOKEN
                changes.append("問%d=全員正解扱い をTACで確定(%r)" % (no, raw))

    return changes, conflicts


# --- 描画 ---------------------------------------------------------------
def build_merged(store):
    merged = []
    for no in range(1, TOTAL_Q + 1):
        if no in store:
            k, v = classify(str(store[no]))
        else:
            k, v = "unpub", None
        if k == "num":
            merged.append({"no": no, "kind": "num", "value": v, "disp": str(v)})
        elif k in ("allcorrect", "special"):
            merged.append({"no": no, "kind": "allcorrect", "value": str(store[no]), "disp": "※"})
        else:
            merged.append({"no": no, "kind": "unpub", "value": None, "disp": "ー"})
    return merged


def determined_count(merged):
    return sum(1 for m in merged if m["kind"] != "unpub")


def answer_section_body(merged):
    determined = determined_count(merged)
    complete = determined == TOTAL_Q
    if complete:
        note = ('<p class="sokuhou-answer-note">自己採点用の参考解答です。'
                '公式の正解ではありません。</p>')
    else:
        note = ('<p class="sokuhou-answer-note">現在判明している問から順次掲載しています'
                '（%d/%d問）。「ー」は判明待ちです。自己採点用の参考解答で、'
                '公式の正解ではありません。</p>' % (determined, TOTAL_Q))
    rows = []
    for start in range(1, TOTAL_Q + 1, 10):
        cells = ""
        for no in range(start, start + 10):
            m = merged[no - 1]
            b = ('<b class="is-wait">ー</b>' if m["kind"] == "unpub"
                 else '<b>%s</b>' % m["disp"])
            cells += '<span class="sokuhou-ans-pair">問%d%s</span>' % (no, b)
        rows.append('<tr><th>問%d〜問%d</th><td>%s</td></tr>' % (start, start + 9, cells))
    table = ('<table class="seo-info-table sokuhou-ans-table"><thead><tr><th>問</th>'
             '<th>解答</th></tr></thead><tbody>%s</tbody></table>' % "".join(rows))
    foot = ""
    if any(m["disp"] == "※" for m in merged):
        foot += ('<p class="sokuhou-answer-note">※ は出題団体の判断等により複数正解・'
                 '全員正解として扱われた可能性がある問題です。正式には公式の発表でご確認ください。</p>')
    if not complete:
        foot += ('<p class="sokuhou-answer-note">下の自己採点は、判明している問だけで'
                 '現時点の得点を計算できます（未判明の問は判明後に反映）。</p>')
    return note + table + foot


def records_json(merged):
    """判明分は correct 付き、未判明は pending:true。判明分だけで採点できる。"""
    out = []
    for m in merged:
        d = {"no": m["no"], "label": "問%d" % m["no"], "points": 1, "choices": 4}
        if m["kind"] == "num":
            d["correct"] = m["value"]
        elif m["kind"] == "allcorrect":
            d["correct"] = "-"
            d["allCorrect"] = True
        else:  # 未判明
            d["pending"] = True
        d["field"] = ""
        out.append(d)
    return json.dumps(out, ensure_ascii=False)


def apply_to_page(merged):
    with open(TARGET, encoding="utf-8") as f:
        src = f.read()
    orig = src
    complete = determined_count(merged) == TOTAL_Q

    new, n1 = re.subn(
        r'(<h2 id="sokuhou-sec-answers">解答一覧</h2>)(.*?)(</section>)',
        lambda mm: mm.group(1) + answer_section_body(merged) + mm.group(3),
        src, count=1, flags=re.S)
    if n1 != 1:
        return ("error", "解答一覧セクションが見つかりません。")
    src = new

    payload = records_json(merged)  # 判明分があれば常に投入（部分採点可）
    src, n2 = re.subn(
        r'(<script type="application/json" id="sokuhou-answers">)(.*?)(</script>)',
        lambda mm: mm.group(1) + payload + mm.group(3), src, count=1, flags=re.S)
    if n2 != 1:
        return ("error", "sokuhou-answers が見つかりません。")

    today = datetime.date.today().isoformat()
    src = re.sub(r'最終更新日：\d{4}-\d{2}-\d{2}', '最終更新日：' + today, src)
    src = re.sub(r'(<th>最終更新日</th><td>)\d{4}-\d{2}-\d{2}(</td>)',
                 lambda mm: mm.group(1) + today + mm.group(2), src)

    if src != orig:
        with open(TARGET, "w", encoding="utf-8") as f:
            f.write(src)
        return ("ok-complete" if complete else "ok-partial",
                "全50問反映・自己採点有効化" if complete else "判明分を反映(自己採点は準備中)")
    return ("nochange", "ページ変更なし")


def save_snapshot(raws, tac_vals, aga_vals, store):
    os.makedirs(SNAP_DIR, exist_ok=True)
    stamp = datetime.datetime.now().strftime("%Y%m%d-%H%M%S")
    for name, raw in raws.items():
        if raw:
            with open(os.path.join(SNAP_DIR, "%s-%s.html" % (name, stamp)), "w",
                      encoding="utf-8") as f:
                f.write(raw)
    summary = {
        "fetched_at": stamp,
        "tac": {str(n): tac_vals.get(n, "") for n in range(1, TOTAL_Q + 1)},
        "agaroot": {str(n): aga_vals.get(n, "") for n in range(1, TOTAL_Q + 1)},
        "store": {str(n): store.get(n, "") for n in range(1, TOTAL_Q + 1)},
    }
    with open(os.path.join(SNAP_DIR, "summary-%s.json" % stamp), "w",
              encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    return stamp


def count_num(vals):
    return sum(1 for n in range(1, TOTAL_Q + 1) if classify(vals.get(n, ""))[0] == "num")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true")
    ap.add_argument("--apply", action="store_true")
    args = ap.parse_args()
    if not (args.check or args.apply):
        ap.error("--check か --apply を指定してください")

    raw_tac = fetch(TAC_URL)
    raw_aga = fetch(AGAROOT_URL)
    tac_vals = parse_tac_answers(raw_tac) if raw_tac else {}
    aga_vals = parse_agaroot_answers(raw_aga) if raw_aga else {}
    tac_meta = parse_tac_meta(raw_tac) if raw_tac else {}

    store = load_store()
    changes, conflicts = ingest(store, tac_vals, aga_vals)
    merged = build_merged(store)
    det = determined_count(merged)

    print("=== 取得・集約結果 ===")
    print("TAC 取得     :", "OK" if raw_tac else "失敗", "/ 数字", count_num(tac_vals), "問",
          "/ 更新:", tac_meta.get("更新日時", "-"))
    print("agaroot 取得 :", "OK" if raw_aga else "失敗", "/ 数字", count_num(aga_vals), "問")
    print("ストア判明数 :", det, "/", TOTAL_Q, "(全問判明=%s)" % (det == TOTAL_Q))
    print("解答 :", " ".join("%d:%s" % (m["no"], m["disp"]) for m in merged))
    if changes:
        print("今回の更新 :")
        for c in changes:
            print("  +", c)
    if conflicts:
        print("---- 要確認(ソース不一致) ----")
        for c in conflicts:
            print("  !", c)

    if args.check:
        print("STATUS:", "COMPLETE" if det == TOTAL_Q else ("PARTIAL(%d)" % det if det else "NONE"))
        sys.exit(0 if det > 0 else 2)

    # --apply
    stamp = save_snapshot({"tac": raw_tac, "agaroot": raw_aga}, tac_vals, aga_vals, store)
    print("スナップショット:", stamp)
    if det == 0:
        print("STATUS: NONE — 判明ゼロのため変更なし。")
        sys.exit(2)
    if changes:  # 実際に解答が増減したときだけストアを保存(無駄なタイムスタンプ更新を防ぐ)
        save_store(store)
    status, msg = apply_to_page(merged)
    print("APPLY:", status, "-", msg)
    if status == "error":
        sys.exit(5)
    sys.exit(0)


if __name__ == "__main__":
    main()
